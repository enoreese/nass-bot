import os
from pathlib import Path
import pinecone
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
from langchain.embeddings import HuggingFaceEmbeddings
from .utils import pretty_log

INDEX_NAME = os.environ.get("INDEX_NAME")
VECTOR_DIR = Path("/vectors")


class PineVectorStore:
    def __init__(self, batch_size=64):
        self.batch_size = batch_size
        self.embedding_engine = self.get_embedding_engine()
        self.vector_index = self.connect_to_vector_index()

    def connect_to_vector_index(self):
        """Adds the texts and metadatas to the vector index."""
        pinecone.init(
            api_key=os.environ["PINECONE_API_KEY"],  # find at app.pinecone.io
            environment=os.environ["PINECONE_ENV"]  # next to api key in console
        )
        index = pinecone.Index(INDEX_NAME)
        vector_index = Pinecone(index, self.embedding_engine.embed_query, "text")
        return vector_index

    def get_embedding_engine(self, model="text-embedding-ada-002", **kwargs):
        """Retrieves the embedding engine."""
        model_name = "sentence-transformers/all-mpnet-base-v2"
        model_kwargs = {'device': 'cpu'}
        embedding_engine = HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs)
        # OpenAIEmbeddings(model=model, **kwargs)
        return embedding_engine

    def create_vector_index(self, documents, ids, metadatas):
        """Creates a vector index that offers similarity search."""
        index = Pinecone.from_texts(
            texts=documents, embedding=self.embedding_engine, ids=ids, metadatas=metadatas, index_name=INDEX_NAME,
            batch_size=self.batch_size
        )
        return index

    def add_to_vector(self, results):
        pretty_log(f"Adding {len(results)} to vector store")
        texts, ids, metadatas = zip(*results)

        ids = [item for sublist in ids for item in sublist]
        texts = [item for sublist in texts for item in sublist]
        metadatas = [item for sublist in metadatas for item in sublist]

        self.vector_index.add_texts(
            texts=texts, metadatas=metadatas, ids=ids, batch_size=self.batch_size
        )
        return True


class FaissVectorStore:
    def __init__(self, batch_size=64):
        self.batch_size = batch_size
        self.embedding_engine = None
        self.lang_embedding_engine = None

        self.get_embedding_engine()
        # self.vector_index = self.connect_to_vector_index()

    def connect_to_vector_index(self):
        """Adds the texts and metadatas to the vector index."""
        from langchain.vectorstores import FAISS

        vector_index = FAISS.load_local(str(VECTOR_DIR), self.lang_embedding_engine, INDEX_NAME)

        return vector_index

    # def load_vector_index(self):
    #     from langchain.vectorstores import FAISS
    #
    #     vector_index = FAISS(self.embedding_engine, INDEX_NAME, docstore, index_to_docstore_id)
    #
    #     return vector_index

    def get_embedding_engine(self, model="all-MiniLM-L6-v2", **kwargs):
        """Retrieves the embedding engine."""
        model_name = "sentence-transformers/all-mpnet-base-v2"
        self.embedding_engine = SentenceTransformer(model)
        self.lang_embedding_engine = HuggingFaceEmbeddings(model_name=model)
        # OpenAIEmbeddings(model=model, **kwargs)

    def create_vector_index(self, documents, ids, metadatas):
        """Creates a vector index that offers similarity search."""
        from langchain import FAISS

        self.wipe_index()

        index = FAISS.from_texts(
            texts=documents, embedding=self.embedding_engine, metadatas=metadatas, ids=ids
        )
        self.save_local_index(index)
        return index

    @staticmethod
    def save_local_index(index):
        index.save_local(folder_path=str(VECTOR_DIR), index_name=INDEX_NAME)
        pretty_log(f"vector store {INDEX_NAME} saved")

    @staticmethod
    def wipe_index():
        files = VECTOR_DIR.glob(f"{INDEX_NAME}.*")
        if files:
            for file in files:
                file.unlink()
            pretty_log("existing index wiped")

    def multi_encode_texts(self, texts):
        # Start the multi-process pool on all available CUDA devices
        pool = self.embedding_engine.start_multi_process_pool()

        # Compute the embeddings using the multi process pool
        emb = self.embedding_engine.encode_multi_process(texts, pool)
        pretty_log(f"Embeddings computed. Shape: {emb.shape}")

        # Optional: Stop the proccesses in the pool
        self.embedding_engine.stop_multi_process_pool(pool)
        return emb.tolist()

    def add_embedding(self, texts, embeddings, ids, metadatas):
        from langchain import FAISS

        self.wipe_index()
        text_embedding_pairs = list(zip(texts, embeddings))
        index = FAISS.from_embeddings(
            text_embeddings=text_embedding_pairs, embedding=self.lang_embedding_engine, metadatas=metadatas, ids=ids
        )
        self.save_local_index(index)
        return index
