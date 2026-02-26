########################################################################################################################
# Project installation
########################################################################################################################
ifneq (,$(wildcard .env))
    include .env
    export
endif

install:
	uv sync

########################################################################################################################
# Deployment
########################################################################################################################

build-image:
	docker build . -t chainlit \
		--build-arg EMBEDDING_MODEL=${EMBEDDING_MODEL}\
		--build-arg SPARSE_EMBEDDING_MODEL=${SPARSE_EMBEDDING_MODEL}\
		--build-arg LANGUAGE_MODEL=${LANGUAGE_MODEL} \
		--build-arg MISTRAL_KEY=${MISTRAL_KEY} \
		--build-arg QDRANT_KEY=${QDRANT_KEY} \
		--build-arg QDRANT_URL=${QDRANT_URL} \
		--build-arg QDRANT_COLLECTION=${QDRANT_COLLECTION} \
		--build-arg LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY} \
		--build-arg LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY} \
		--build-arg LANGFUSE_HOST_URL=${LANGFUSE_HOST_URL} \
		--build-arg CHUNK_SIZE=${CHUNK_SIZE} \
		--build-arg CHUNK_OVERLAP=${CHUNK_OVERLAP} \
		--build-arg TOP_K=${TOP_K} \
		--build-arg THRESHOLD=${THRESHOLD} \
		--build-arg VERBOSE=${VERBOSE}
