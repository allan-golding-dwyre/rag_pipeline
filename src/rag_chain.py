import contextlib
from operator import itemgetter
from pathlib import Path
from typing import List, Any

from langchain_community.cross_encoders import HuggingFaceCrossEncoder
# https://www.datacamp.com/fr/courses/retrieval-augmented-generation-rag-with-langchain
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnableConfig
from langchain_classic.retrievers import ContextualCompressionRetriever

from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
from qdrant_client import QdrantClient

import config
from rich import print

from cross_encoder_rerank_threshold import CrossEncoderRerankerThreshold

PROMPT_DIR = Path("prompts")
STRICT_PROMPT_PATH = PROMPT_DIR / "INSTRUCTION_STRICT.md"
CHATTY_PROMPT_PATH = PROMPT_DIR / "INSTRUCTION_CHATTY.md"

# TODO : [ ] Batching embedding to VectorStore
# TODO : [ ] Change reranker from HuggingFace to CohereRerank [Cohere](https://cohere.com/fr)

class RAGChain:
    def __init__(self):
        print("init the RAG chain")
        self.vector_store = self._setup_vector_store()
        self.retriever = self._build_retriever()
        self.chain = self._create_chain()

    async def ask(self, question: Any, chat_history: List[dict], session_id = -1):
        print(f"Question asked '{question}'")
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
        # pour supprimer les erreurs qui ne viennent pas de nous
        with contextlib.redirect_stderr(open('/dev/null', 'w')):
            async for chunk in stream:
                yield chunk

    def _build_retriever(self) :
        base_retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": config.TOP_K * 2, }
        )
        cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        # NOTE : pour plus tard : CohereRerank (api payante) alternative local :
        reranker = CrossEncoderRerankerThreshold(model=cross_encoder, top_n=config.TOP_K, threshold=config.THRESHOLD)
        return ContextualCompressionRetriever(
            base_retriever=base_retriever,
            base_compressor=reranker
        )

    @staticmethod
    def _setup_vector_store() -> QdrantVectorStore:
        embedding = MistralAIEmbeddings(model=config.EMBEDDING_MODEL, api_key=config.MISTRAL_KEY)
        sparse_embedding = FastEmbedSparse(model_name=config.SPARSE_EMBEDDING_MODEL)
        client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_KEY, port=None)

        return QdrantVectorStore(
            client=client,
            collection_name=config.QDRANT_COLLECTION,
            retrieval_mode=RetrievalMode.HYBRID,
            embedding=embedding,
            sparse_embedding= sparse_embedding,
            sparse_vector_name=config.SPARSE_EMBEDDING_MODEL
        )

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

    def _create_chain(self):
        print("Création de la chaine")
        llm = ChatMistralAI(model_name=config.LANGUAGE_MODEL, api_key=config.MISTRAL_KEY)

        # ici on recup les inputs important
        base = RunnableParallel(
            question=RunnableLambda(itemgetter("question")),
            chat_history=RunnableLambda(itemgetter("chat_history")),
            context_docs=RunnableLambda(itemgetter("question")) | self.retriever
        )

        return (base
                |   self.build_prompt_input()       # format history et contexts
                |   self.select_prompt_template()   # prend à partir de history le bon template
                |   llm                             # génère le message
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

        def format_docs(docs : List[Document]):
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
