from pydantic import SecretStr
from dotenv import load_dotenv
import os

load_dotenv()

# ====== Models ======
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LANGUAGE_MODEL = os.getenv("LANGUAGE_MODEL")
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
CHUNK_SIZE = os.getenv("CHUNK_SIZE")
CHUNK_OVERLAP = os.getenv("CHUNK_OVERLAP")
TOP_K = os.getenv("TOP_K")
THRESHOLD = os.getenv("THRESHOLD")
VERBOSE = os.getenv("VERBOSE")