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
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP"))
TOP_K = int(os.getenv("TOP_K"))
THRESHOLD = float(os.getenv("THRESHOLD"))
VERBOSE = True if os.getenv("VERBOSE") == "True" else False