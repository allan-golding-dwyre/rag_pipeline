from langchain_mistralai import MistralAIEmbeddings
import uuid

from tqdm import tqdm
from rich import print

from src import config
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams, Modifier, PointStruct
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from qdrant_client import QdrantClient

from src.base_documentation_loader import BaseDocumentationLoader

class DocumentIndexer:
    def __init__(self, batch_size : int = 64, reset_collection = True):
        self.embedding = MistralAIEmbeddings(model=config.EMBEDDING_MODEL, api_key=config.MISTRAL_KEY)
        self.sparse_embedding = FastEmbedSparse(model_name=config.SPARSE_EMBEDDING_MODEL)
        self.client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_KEY, port=None)
        self.batch_size = batch_size

        self._setup_collection(reset_collection)
        self.vector_store = self._setup_vector_store()

    def _setup_collection(self, reset_collection):
        if reset_collection and self.client.collection_exists(config.QDRANT_COLLECTION):
            self.client.delete_collection(config.QDRANT_COLLECTION)

        if self.client.collection_exists(config.QDRANT_COLLECTION):
            return

        vector_size = len(self.embedding.embed_query("sample text"))
        self.client.create_collection(
            collection_name=config.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            sparse_vectors_config={
                config.SPARSE_EMBEDDING_MODEL : SparseVectorParams(modifier=Modifier.IDF)
            },
        )

    def _setup_vector_store(self):
        return QdrantVectorStore(
            client=self.client,
            collection_name=config.QDRANT_COLLECTION,
            retrieval_mode=RetrievalMode.HYBRID,
            embedding=self.embedding,
            sparse_embedding= self.sparse_embedding,
            sparse_vector_name=config.SPARSE_EMBEDDING_MODEL
        )

    @staticmethod
    def _token_len(text: str) -> int:
        return int(len(text.split()) / 0.75)

    def index_documents(self, loader : BaseDocumentationLoader):
        print("Chargements des documents ...")
        docs = loader.load()
        print("Documents trouvées :", len(docs))

        print("Embedding des documents")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=self._token_len,
            separators=["\n\n", "\n", " "],
        )

        chunks = splitter.split_documents(docs)
        print("Nombres de chunks créer :", len(chunks))
        print(chunks[0])

        # === Batching des chunks ===
        batch_size = self.batch_size
        for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
            batch_chunks = chunks[i:(i + batch_size)]
            self.vector_store.add_documents(batch_chunks)

        print("\nDocuments embedded")
