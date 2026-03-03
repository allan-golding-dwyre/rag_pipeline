from pydantic import SecretStr
from dotenv import load_dotenv
import os

load_dotenv()

# ====== Models ======
# EMBEDDING_MODEL='hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
# LANGUAGE_MODEL='hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
EMBEDDING_MODEL='mistral-embed'
SPARSE_EMBEDDING_MODEL='Qdrant/bm25'
LANGUAGE_MODEL='mistral-small-2506'

# --- Auth ---
MISTRAL_KEY = SecretStr(os.getenv("MISTRAL_KEY"))

# ====== Qdrant ======
# --- Auth ---
QDRANT_KEY = os.getenv("QDRANT_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
# --- Collection ---
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

# ====== Langfuse ======
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST_URL = os.getenv("LANGFUSE_HOST_URL")

# ====== SETTINGS ======
CHUNK_SIZE=400
CHUNK_OVERLAP=100
TOP_K=4
THRESHOLD=0.4
VERBOSE=False

# --- online fetching ---
CHAPTERS_TO_FETCH = ["About", "Manual", "Class reference"]