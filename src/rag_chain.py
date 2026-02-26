from operator import itemgetter
from pathlib import Path
from typing import List, Any

# https://www.datacamp.com/fr/courses/retrieval-augmented-generation-rag-with-langchain
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnableConfig

# from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

import config
from documentation_loader import DocumentationLoader

from rich import print

PROMPT_DIR = Path("prompts")
STRICT_PROMPT_PATH = PROMPT_DIR / "INSTRUCTION_STRICT.md"
CHATTY_PROMPT_PATH = PROMPT_DIR / "INSTRUCTION_CHATTY.md"

# TODO : [ ] SPARSE + Compressed reranker
# TODO : [x] Environnement D'api keys
# TODO : [x] Langfuse
# TODO : [ ] Fetch from url when embedding (get the most updated version of documentation) -> (https://selenium-python.readthedocs.io/installation.html)
# TODO : [x] Dockerfile, Makefile

class RAGChain:
    def __init__(self, documents_path="documents", force_push=False):
        print("init the RAG chain")
        #self.threshold = config.THRESHOLD
        self.documents_paths = list(Path(documents_path).glob("*.html"))

        self.embedding = MistralAIEmbeddings(model=config.EMBEDDING_MODEL, api_key=config.MISTRAL_KEY)
        self.llm = ChatMistralAI(model_name=config.LANGUAGE_MODEL, api_key=config.MISTRAL_KEY)

        self.client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_KEY, port=None)
        self.vector_store = self._setup_vector_store(force_push)

        #NOTE : Si je fais seulement du Dense
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": config.TOP_K, 'score_threshold': config.THRESHOLD}
        )
        # base_retriever = self.vector_store.as_retriever(
        #     search_type="similarity",
        #     search_kwargs={"k": config.TOP_K * 2,}
        # )
        # NOTE : pour plus tard : CohereRerank (api payante) alternative local :
        # reranker = CrossEncoderReranker(model=c"ross-encoder/ms-marco-MiniLM-L-6-v2", top_n=config.TOP_K)
        #
        #
        # self.retriever = ContextualCompressionRetriever(
        #     base_compressor=reranker,
        #     base_retriever=hybrid_retriever
        # )

        self.chain = self._create_chain()

    async def ask(self, question: Any, chat_history: List[dict], session_id = -1):
        inputs = {
            "question": question,
            "chat_history": chat_history,
        }
        # --- Traceability ---
        handler = LangfuseCallbackHandler()
        stream_config = RunnableConfig(
            callbacks=[handler],
            metadata={
                "session_id": session_id,
                "feature": "rag_chat"
            }
        )

        # --- Async call to the pipeline ---
        stream = self.chain.astream(inputs, config=stream_config)
        async for chunk in stream:
            yield chunk



    def _setup_vector_store(self, force_push=False):
        vector_size = len(self.embedding.embed_query("sample text"))
        collection_exists = self.client.collection_exists(config.QDRANT_COLLECTION)

        if force_push:
            self.client.delete_collection(config.QDRANT_COLLECTION)
            collection_exists = False

        if not collection_exists:
            self.client.create_collection(
                collection_name=config.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=config.QDRANT_COLLECTION,
            embedding=self.embedding,
        )

        if collection_exists:
            return vector_store

        print("embedding des documents")

        docs = DocumentationLoader(self.documents_paths, verbose=config.VERBOSE).load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )

        chunks = splitter.split_documents(docs)
        vector_store.add_documents(chunks)
        print("VectorStore crée")

        return vector_store

    @staticmethod
    def _make_chat_prompt_from_file(prompt_file_path: Path):
        prompt_str = prompt_file_path.read_text(encoding="utf-8")

        return ChatPromptTemplate.from_messages(
            [
                ("system", prompt_str),
                ("system", "Contexte (extraits récupérés):\n{context}"),
                MessagesPlaceholder("chat_history"),
                ("human", "{question}"),
            ]
        )

    # def _search_with_scores(self, question: str) -> List[Document]:
    #     results = self.vector_store.similarity_search_with_score(
    #         question, k=config.TOP_K
    #     )
    #     docs = []
    #     for doc, score in results:
    #         doc.metadata["score"] = score
    #         docs.append(doc)
    #     return docs

    def _create_chain(self):
        print("Création de la chaine")

        # ici on recup les inputs important
        base = RunnableParallel(
            question=RunnableLambda(itemgetter("question")),
            chat_history=RunnableLambda(itemgetter("chat_history")),
            context_docs=RunnableLambda(itemgetter("question")) | self.retriever
        )

        return (base
                |   self.build_prompt_input()       # format history et contexts
                |   self.select_prompt_template()   # prend à partir de history le bon template
                |   self.llm                        # génère le message
                |   StrOutputParser()               # l'envoie a chainlit
        )

    def select_prompt_template(self):
        def select_prompt(x ):
            msgs = x.get("chat_history", [])
            # Si dans la conversation, il y un message de assistant (ia)
            has_assistant = any(
                getattr(m, "role", "") == "assistant"
                for m in msgs
            )

            prompt_file_path = CHATTY_PROMPT_PATH if has_assistant else STRICT_PROMPT_PATH
            return self._make_chat_prompt_from_file(prompt_file_path)

        return RunnableLambda(select_prompt)

    ## Génère permet juste de garder la question et formater les chats, et contexts
    @staticmethod
    def build_prompt_input():
        def get_message_from_role(role, msg):
            if role == "user":
                return HumanMessage(content=msg)
            return AIMessage(content=msg)

        def format_history(history):
            last_messages = history[-8:]
            msgs = [
                get_message_from_role(m["role"], m["content"])
                for m in last_messages
            ]
            return msgs

        # def get_score(doc):
        #     return (
        #             doc.metadata.get("score")
        #             or doc.metadata.get("relevance_score")
        #             or doc.metadata.get("distance")
        #     )

        def format_docs(docs : List[Document]):
            # filtered_docs = [doc for doc in docs if self.threshold < get_score(doc) ]
            formatted_docs = []
            for doc in docs:

                flat_text = "; ".join(f"{k}: {v}" for k, v in doc.metadata.items())
                flat_text = f'<<{doc.page_content.strip()}>>\ncontent info => {flat_text}'

                formatted_docs.append(flat_text)

            return "\n\n".join(formatted_docs) if formatted_docs else "(aucun extrait pertinent trouvé)"

        return RunnableLambda(lambda x: {
                "question" :        x["question"],
                "chat_history" :    format_history(x["chat_history"]),
                "context" :         format_docs(x["context_docs"]),
            }
        )
