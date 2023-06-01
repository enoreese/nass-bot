import os
from pathlib import Path
import pymongo
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pdfminer.pdfparser import PDFSyntaxError, PSEOF
from botocore.exceptions import ConnectionClosedError
import IPython
import modal

load_dotenv()

VECTOR_DIR = Path("/vectors")
vector_storage = modal.shared_volume.SharedVolume().persist("vector-vol")

# definition of our container image for jobs on Modal
# Modal gets really powerful when you start using multiple images!
image = modal.image.Image.debian_slim(  # we start from a lightweight linux distro
    python_version="3.10"  # we add a recent Python version
).pip_install(  # and we install the following packages:
    "langchain",
    # 🦜🔗: a framework for building apps with LLMs
    "openai",
    # high-quality language models and cheap embeddings
    "tiktoken",
    # tokenizer for OpenAI models
    "pinecone-client",
    # vector storage and similarity search
    "pymongo",
    # python client for MongoDB, our data persistence solution
    "gradio",
    # simple web UIs in Python, from 🤗
    "gantry",
    # 🏗️: monitoring, observability, and continual improvement for ML systems
    "boto3",
    "python-dotenv",
    "requests",
    "pdfplumber",
    "tqdm_batch",
    "joblib",
    "sentence_transformers",
    "faiss-cpu"
)

# we define a Stub to hold all the pieces of our app
# most of the rest of this file just adds features onto this Stub
stub = modal.stub.Stub(
    name="nass-vec",
    image=image,
    secrets=[
        # this is where we add API keys, passwords, and URLs, which are stored on Modal
        modal.secret.Secret.from_name("openai-api-key"),
        modal.secret.Secret.from_name("my-pinecone-secret"),
        # modal.Secret.from_name("gantry-api-key"),
        modal.secret.Secret.from_name("my-aws-secret"),
        modal.secret.Secret.from_name("my-mongodb-secret")
    ],
    mounts=[
        modal.mount.Mount.from_local_dir("/Users/osasusen/Dev/nass-bot/nassbot_app/utils", remote_path="/root/utils/"),
modal.mount.Mount.from_local_dir("/Users/osasusen/Dev/nass-bot/nassbot_app/chains", remote_path="/root/chains/"),
    ],
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


def get_doc_from_mongo():
    docs = collection.find({})
    return docs


@stub.function(
    image=image,
    timeout=500,
    shared_volumes={
        str(VECTOR_DIR): vector_storage,
    },
    gpu=modal.gpu.T4(count=4),
    cpu=8.0,  # use more cpu for vector storage creation
)
def sync_vector_db_to_doc_db():
    """Syncs the vector index onto the document storage."""
    from utils import vecstore
    from utils import utils
    from multiprocessing import Pool

    num_workers = 100
    vector_store = vecstore.FaissVectorStore()
    utils.pretty_log("connected to vector store")

    try:
        docs = utils.get_json_from_s3("nass-bot", "json_files/mongo_document.json")
    except:
        docs = list(get_doc_from_mongo())
        utils.save_json_to_s3(docs, "nass-bot", "json_files/mongo_document.json")
    utils.pretty_log("fetched documents from document DB")

    utils.pretty_log("splitting into bite-size chunks")
    try:
        results = utils.read_joblib_from_s3("nass-bot", "pdf_files/splitted_corpus.data")
    except:
        pool = Pool(num_workers)

        results = pool.map(prep_documents_for_vector_storage, docs)
        pool.close()
        utils.save_joblib_to_s3(results, "nass-bot", "pdf_files/splitted_corpus.data")

    texts, ids, metadatas = zip(*results)

    texts = [item for sub_list in texts for item in sub_list]
    ids = [item for sub_list in ids for item in sub_list]
    metadatas = [item for sub_list in metadatas for item in sub_list]

    utils.pretty_log("Getting text embeddings...")
    embeddings = vector_store.multi_encode_texts(texts)

    utils.pretty_log(f"sending {len(embeddings)} total instances to vector store {vecstore.INDEX_NAME}")
    utils.pretty_log(f"vector store created")


def prep_documents_for_vector_storage(document):
    """Prepare documents from document store for embedding and vector storage.

    Documents are split into chunks so that they can be used with sourced Q&A.

    Arguments:
        document: A list of LangChain.Documents with text, metadata, and a hash ID.
    """
    from utils import utils
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500, chunk_overlap=100, allowed_special="all"
    )
    try:
        text = utils.get_pdf_text(document["doc_type"], document["metadata"]["doc_id"])
    except (PDFSyntaxError, PSEOF, ConnectionClosedError):
        utils.pretty_log(f"PDFSyntaxError|PSEOF on {document['doc_type']}-{document['metadata']['doc_id']}")
        text = document["title"]

    doc_texts = text_splitter.split_text(text)
    ids = [str(document["_id"]) for _ in range(len(doc_texts))]
    metadata = [document["metadata"] for _ in range(len(doc_texts))]
    return doc_texts, ids, metadata


@stub.function(
    image=image,
    interactive=True,
)
def debug():
    """Convenient debugging access to Modal."""

    IPython.embed()


@stub.function(
    image=image,
    shared_volumes={
        str(VECTOR_DIR): vector_storage,
    },
)
@stub.web_endpoint(method="GET", label="nass-bot-hook")
def web(query: str, request_id=None):
    from utils import utils
    from chains import qa_chain

    """Exposes our Q&A chain for queries via a web endpoint."""
    utils.pretty_log(
        f"handling request with client-provided id: {request_id}"
    ) if request_id else None
    answer = qa_chain.qanda_langchain(query, request_id=request_id, with_logging=True)
    return {
        "answer": answer,
    }


@stub.function(
    image=image,
    shared_volumes={
        str(VECTOR_DIR): vector_storage,
    },
)
def cli(query: str):
    from utils import utils
    from chains import qa_chain

    answer = qa_chain.qanda_langchain(query, with_logging=False)
    utils.pretty_log(f"🦜 ANSWER 🦜 \n {answer}")
