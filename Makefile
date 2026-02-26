########################################################################################################################
# Project installation
########################################################################################################################

install:
	uv sync

########################################################################################################################
# Deployment
########################################################################################################################

build-image:
	docker build . -t chainlit --build-arg OPENAI_API_KEY=${OPENAI_API_KEY} --build-arg MISTRAL_API_KEY=${MISTRAL_API_KEY} --build-arg QDRANT_URL=${QDRANT_URL} --build-arg QDRANT_API_KEY=${QDRANT_API_KEY} --build-arg COHERE_API_KEY=${COHERE_API_KEY} --build-arg LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY} --build-arg LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY} --build-arg LANGFUSE_BASE_URL=${LANGFUSE_BASE_URL} --build-arg DATABASE_URL=${DATABASE_URL}