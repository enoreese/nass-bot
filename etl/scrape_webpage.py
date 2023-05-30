from bs4 import BeautifulSoup
import boto3
import requests
import pandas as pd
import json
import os
import modal
from pathlib import Path
from dotenv import load_dotenv
import pymongo
from pymongo import InsertOne, UpdateOne

load_dotenv()

WEBPAGE_DIR = Path("/Users/osasusen/Dev/nass-bot/etl/webpages/")

# definition of our container image for jobs on Modal
# Modal gets really powerful when you start using multiple images!
image = modal.image.Image.debian_slim(  # we start from a lightweight linux distro
    python_version="3.10"  # we add a recent Python version
).pip_install(  # and we install the following packages:
    "boto3",
    "pandas",
    "requests",
    "python-dotenv",
    "pymongo[srv]",
    "beautifulsoup4",
    "fsspec",
    "s3fs"
)

# we define a Stub to hold all the pieces of our app
# most of the rest of this file just adds features onto this Stub
stub = modal.stub.Stub(
    name="nass-etl",
    image=image,
    secrets=[
        # this is where we add API keys, passwords, and URLs, which are stored on Modal
        modal.secret.Secret.from_name("my-aws-secret"),
        modal.secret.Secret.from_name("my-mongodb-secret")
    ],
    mounts=[modal.mount.Mount.from_local_dir(str(WEBPAGE_DIR), remote_path="/root/webpages/")]
)

mongodb_url = os.environ["MONGODB_URI"]
mongodb_user = os.environ["MONGODB_USER"]
mongodb_password = os.environ["MONGODB_PASSWORD"]
CHUNK_SIZE = 150
CONNECTION_STRING = f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_url}/?retryWrites=true&w=majority"

# connect to the database server
client = pymongo.MongoClient(CONNECTION_STRING)
# connect to the database
db = client.get_database("nass_bot")
# get a representation of the collection
collection = db.get_collection("corpus")


def get_pdf_save_to_s3(url, sub_dir, doc_id):
    """
    Fetches a PDF file from a URL and saves it to S3 and return the s3 path
    """
    print(f"Fetching {url}...")
    s3 = boto3.client('s3')
    bucket = 'nass-bot'
    key = f'pdf_files/{sub_dir}/{doc_id}.pdf'
    # check if key exists
    try:
        s3.head_object(Bucket=bucket, Key=key)
        print("File already exists in S3")
        return f's3://{bucket}/{key}'
    except:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            s3.upload_fileobj(r.raw, bucket, key)
            return f's3://{bucket}/{key}'
        else:
            return None


webpages = {
    "bills": "/root/webpages/National Assembly _ Federal Republic of Nigeria.html",
    "hansard": "/root/webpages/National Assembly _ Federal Republic of Nigeria-hansard.html",
    "order_papers": "/root/webpages/National Assembly _ Federal Republic of Nigeria - order_paper.html",
    "votes_and_proceedings": "/root/webpages/National Assembly _ Federal Republic of Nigeria - votes_proceding.html",
}


def scrape_page():
    data = []
    for sub_dir, webpage in webpages.items():
        print(f"Scraping {sub_dir}...")
        with open(webpage) as html_file:
            soup = BeautifulSoup(html_file, "html")
            table = soup.find("table", attrs={'class': 'table table-striped table-bordered dataTable'})
            table_body = table.find('tbody')
            table_rows = table_body.find_all("tr")
            for tr in table_rows:
                td = tr.find_all("td")
                url = str(td[0].find('a')['href'])
                _id = url.split('/')[-1]
                if sub_dir == "bills":
                    obj = {
                        'title': td[0].text,
                        'url': url,
                        'metadata': {
                            'chamber': str(td[1].text),
                            'first_reading': str(td[2].text),
                            'second_reading': str(td[3].text),
                            'commitee_referred': str(td[4].text),
                            'third_reading': str(td[5].text),
                            'download_url': f'https://nass.gov.ng/documents/billdownload/{_id}.pdf',
                            'doc_id': _id
                        },
                        'doc_type': 'bills'
                    }
                else:
                    obj = {
                        'title': td[0].text,
                        'url': url,
                        'metadata': {
                            'chamber': str(td[1].text),
                            'document_date': str(td[2].text),
                            'parliament': str(td[3].text),
                            'session': str(td[4].text),
                            'download_url': url,
                            'doc_id': _id
                        },
                        'doc_type': sub_dir
                    }
                data.append(obj)
    df = pd.DataFrame(data)
    df.to_json('s3://nass-bot/json_files/corpus_document.json', orient='records', index=True)
    df_json = df.to_json(orient='records', index=True)
    return df_json


def save_to_mongodb(documents):
    print("Saving to MongoDB...")

    requesting = []

    for document in documents:
        requesting.append(InsertOne(document))

        if len(requesting) >= CHUNK_SIZE:
            collection.bulk_write(requesting)
            requesting = []

    if requesting:
        collection.bulk_write(requesting)
        requesting = []

    return True


def get_doc_from_mongo():
    docs = collection.find({})
    return docs


@stub.function(
    image=image,
    timeout=1000,
)
def main():
    print("Starting ETL...")
    documents = json.loads(scrape_page())
    save_to_mongodb(documents)


def download_pdf(document):
    print(f"Downloading PDF {document['metadata']['doc_id']}...")
    url = document['metadata']['download_url']
    doc_id = document['metadata']['doc_id']
    sub_dir = document['doc_type']
    s3_path = get_pdf_save_to_s3(url, sub_dir, doc_id)
    document['metadata']['s3_path'] = s3_path
    UpdateOne({'_id': document['_id']}, {'$set': {'metadata.s3_path': s3_path}})
    return document


@stub.function(
    image=image,
    timeout=1000,
    retries=3,
    cpu=8.0,
)
def download_pdfs():
    print("Starting PDF ETL...")
    documents = list(get_doc_from_mongo())
    print(len(documents))
    from multiprocessing import Pool
    pool = Pool(10)
    pool.map(download_pdf, documents)
