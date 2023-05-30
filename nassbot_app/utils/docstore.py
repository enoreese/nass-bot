MONGO_COLLECTION = "corpus"


def get_documents(client, db="nass_bot", collection=MONGO_COLLECTION):
    """Fetches a collection of documents from a document database."""
    db = client[db]
    collection = db["corpus"]
    docs = list(collection.find({}))
    print(docs[0])
    return docs


def connect():
    """Connects to a document database, here MongoDB."""
    import os
    from pymongo.mongo_client import MongoClient
    from pymongo.server_api import ServerApi

    mongodb_password = os.environ["MONGODB_PASSWORD"]
    mongodb_user = os.environ["MONGODB_USER"]
    mongodb_uri = os.environ["MONGODB_URI"]
    connection_string = f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_uri}/?retryWrites=true&w=majority"
    client = MongoClient(connection_string, server_api=ServerApi('1'))
    return client
