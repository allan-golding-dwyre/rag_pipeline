FROM python:3.12-slim
LABEL authors="allan.golding-dwyre@vidal.fr"

# ====== Models ======
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


# ============ DEFINE ENV ============
ENV MISTRAL_KEY=${MISTRAL_KEY} \
    QDRANT_KEY=${QDRANT_KEY} \
    QDRANT_URL=${QDRANT_URL} \
    QDRANT_COLLECTION=${QDRANT_COLLECTION} \
    LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY} \
    LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY} \
    LANGFUSE_HOST_URL=${LANGFUSE_HOST_URL}

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
CMD ["uv", "run", "chainlit", "run", "src/chainlit_app.py", "--host", "0.0.0.0", "--port", "8000"]
