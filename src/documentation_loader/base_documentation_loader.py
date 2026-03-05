import os
from abc import abstractmethod, ABC
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Iterable

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from tqdm import tqdm
from rich import print
from src.documentation_loader.doc_parser import GodotDocParser


class BaseDocumentationLoader(BaseLoader, ABC):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.parser = GodotDocParser(verbose)

    @abstractmethod
    def _get_html_sources(self) -> Iterable[str]:
        pass

    def load(self) -> List[Document]:
        documents = []
        futures = []
        total_sources = 0

        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            for content in self._get_html_sources():
                futures.append(executor.submit(self.parser.create_documents, content))
                total_sources += 1

            print(f"Total sources: {total_sources}")
            with tqdm(desc="Processing HTML", unit="file") as bar:
                for future in as_completed(futures):
                    documents.extend(future.result())
                    bar.update(1)

        return documents
