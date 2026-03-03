from __future__ import annotations

import math
import operator
from collections.abc import Sequence

from langchain_core.callbacks import Callbacks
from langchain_core.documents import BaseDocumentCompressor, Document
from pydantic import ConfigDict
from typing_extensions import override
from rich import print

from langchain_classic.retrievers.document_compressors.cross_encoder import (
    BaseCrossEncoder,
)


class CrossEncoderRerankerThreshold(BaseDocumentCompressor):
    """Document compressor that uses CrossEncoder for reranking."""

    model: BaseCrossEncoder
    """CrossEncoder model to use for scoring similarity
      between the query and documents."""
    top_n: int = 3
    """Number of documents to return."""
    threshold: float = 0.0
    """Number of documents to return."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
    )

    @staticmethod
    def sigmoid(x):
        return 1 / (1 + math.exp(-x))

    @override
    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Callbacks | None = None,
    ) -> Sequence[Document]:
        """Rerank documents using CrossEncoder.

        Args:
            documents: A sequence of documents to compress.
            query: The query to use for compressing the documents.
            callbacks: Callbacks to run during the compression process.

        Returns:
            A sequence of compressed documents.
        """
        scores = self.model.score([(query, doc.page_content) for doc in documents])
        docs_with_scores = list(zip(documents, scores, strict=False))

        for doc, score in docs_with_scores:
            doc.metadata["score"] = self.sigmoid(score)

        result = filter(lambda x: x[0].metadata["score"] > self.threshold, docs_with_scores)
        result = sorted(result, key=operator.itemgetter(1), reverse=True)
        print(list(map(lambda x: x[0], result[: self.top_n])))
        return [doc for doc, _ in result[: self.top_n]]
