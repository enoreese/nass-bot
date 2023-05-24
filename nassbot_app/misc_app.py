from utils.modal_utils import stub, image
from utils.utils import pretty_log, vector_storage, VECTOR_DIR

from utils import docstore
from utils import vecstore

from langchain.text_splitter import RecursiveCharacterTextSplitter

import IPython


@stub.function(
    image=image,
    shared_volumes={
        str(VECTOR_DIR): vector_storage,
    },
    cpu=8.0,  # use more cpu for vector storage creation
)
def sync_vector_db_to_doc_db():
    """Syncs the vector index onto the document storage."""

    document_client = docstore.connect()
    pretty_log("connected to document DB")

    embedding_engine = vecstore.get_embedding_engine(allowed_special="all")

    docs = docstore.get_documents(document_client, "fsdl")

    pretty_log("splitting into bite-size chunks")
    ids, texts, metadatas = prep_documents_for_vector_storage(docs)

    pretty_log(f"sending to vector store {vecstore.INDEX_NAME}")
    vector_index = vecstore.create_vector_index(
        vecstore.INDEX_NAME, embedding_engine, texts, metadatas
    )
    vector_index.save_local(folder_path=VECTOR_DIR, index_name=vecstore.INDEX_NAME)
    pretty_log(f"vector store {vecstore.INDEX_NAME} created")


def prep_documents_for_vector_storage(documents):
    """Prepare documents from document store for embedding and vector storage.

    Documents are split into chunks so that they can be used with sourced Q&A.

    Arguments:
        documents: A list of LangChain.Documents with text, metadata, and a hash ID.
    """

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500, chunk_overlap=100, allowed_special="all"
    )
    ids, texts, metadatas = [], [], []
    for document in documents:
        text, metadata = document["text"], document["metadata"]
        doc_texts = text_splitter.split_text(text)
        doc_metadatas = [metadata] * len(doc_texts)
        ids += [metadata.get("sha256")] * len(doc_texts)
        texts += doc_texts
        metadatas += doc_metadatas

    return ids, texts, metadatas


@stub.function(
    image=image,
    interactive=True,
    shared_volumes={
        str(VECTOR_DIR): vector_storage,
    },
)
def debug():
    """Convenient debugging access to Modal."""

    IPython.embed()
