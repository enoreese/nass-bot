import os
import json
import boto3
import pickle
from tempfile import TemporaryFile
from bson import json_util
from botocore.client import Config
import pdfplumber
from io import BytesIO

session = boto3.Session(
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
)

BUCKET = "nass-bot"

config = Config(
    connect_timeout=2000,
    read_timeout=2000,
    retries={'max_attempts': 0}
)


def get_pdf_text(sub_dir, doc_id):
    """Extracts text from a PDF file."""
    s3 = session.resource('s3', config=config)
    obj = s3.Object(BUCKET, f"pdf_files/{sub_dir}/{doc_id}.pdf")
    fs = obj.get()['Body'].read()
    with pdfplumber.open(BytesIO(fs)) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages])
    return text


def save_json_to_s3(json_object, bucket, key):
    pretty_log("Saving docs to s3")
    s3 = session.resource('s3', config=config)
    s3_object = s3.Object(bucket, key)
    s3_object.put(
        Body=json_util.dumps(json_object)
    )


def save_joblib_to_s3(result_object, bucket, key):
    pretty_log("Saving joblib to s3")
    s3 = session.resource('s3', config=config)

    s3_object = s3.Object(bucket, key)
    s3_object.put(
        Body=pickle.dumps(result_object)
    )


def read_joblib_from_s3(bucket, key):
    pretty_log("Getting splitted texts from s3")
    s3 = session.resource('s3', config=config)
    obj = s3.Object(bucket, key)
    fs = obj.get()['Body'].read()
    return pickle.loads(fs)


def get_json_from_s3(bucket, key):
    pretty_log("Getting docs json from s3")
    s3 = session.resource('s3', config=config)
    obj = s3.Object(bucket, key)
    fs = json.loads(obj.get()['Body'].read())
    return fs


def pretty_log(str):
    print(f"{START}🥞: {str}{END}")


def log_event(query, sources, answer, request_id=None):
    """Logs the event to Gantry."""
    import os

    import gantry

    gantry.init(api_key=os.environ["GANTRY_API_KEY"], environment="modal")

    application = "ask-fsdl"
    join_key = str(request_id) if request_id else None

    inputs = {"question": query}
    inputs["docs"] = "\n\n---\n\n".join(source.page_content for source in sources)
    inputs["sources"] = "\n\n---\n\n".join(
        source.metadata["source"] for source in sources
    )
    outputs = {"answer_text": answer}

    record_key = gantry.log_record(
        application=application, inputs=inputs, outputs=outputs, join_key=join_key
    )

    return record_key


# Terminal codes for pretty-printing.
START, END = "\033[1;38;5;214m", "\033[0m"
