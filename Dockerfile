FROM python:3.12-slim
LABEL authors="allan.golding-dwyre@vidal.fr"

# ====== Models ======
ARG EMBEDDING_MODEL
ARG LANGUAGE_MODEL

# --- Auth ---
ARG MISTRAL_KEY

# ====== Qdrant ======
# --- Auth ---
ARG QDRANT_KEY
ARG QDRANT_URL
# --- Collection ---
ARG QDRANT_COLLECTION

# ====== Langfuse ======
ARG LANGFUSE_PUBLIC_KEY
ARG LANGFUSE_SECRET_KEY
ARG LANGFUSE_HOST_URL

# ====== SETTINGS ======
ARG CHUNK_SIZE=400
ARG CHUNK_OVERLAP=100
ARG TOP_K=6
ARG THRESHOLD=0.0
ARG VERBOSE=False

# ============ DEFINE ENV ============
ENV EMBEDDING_MODEL=${EMBEDDING_MODEL} \
    LANGUAGE_MODEL=${LANGUAGE_MODEL} \
    MISTRAL_KEY=${MISTRAL_KEY} \
    QDRANT_KEY=${QDRANT_KEY} \
    QDRANT_URL=${QDRANT_URL} \
    QDRANT_COLLECTION=${QDRANT_COLLECTION} \
    LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY} \
    LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY} \
    LANGFUSE_HOST_URL=${LANGFUSE_HOST_URL} \
    CHUNK_SIZE=${CHUNK_SIZE} \
    CHUNK_OVERLAP=${CHUNK_OVERLAP} \
    TOP_K=${TOP_K} \
    THRESHOLD=${THRESHOLD} \
    VERBOSE=${VERBOSE}

# ============ SETUP IMAGE DEPENDANCY ============
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-cache

# ============ COPY NEEDED FILES ============

COPY src ./src
COPY .chainlit ./.chainlit
COPY public ./public
COPY documents ./documents
COPY prompts ./prompts

EXPOSE 8080
CMD ["uv", "run", "chainlit", "run", "src/chainlit_app.py"]