#uv run chainlit run src/chainlit_app.py
from pathlib import Path

from src.document_indexer import DocumentIndexer
from src.file_documentation_loader import FileDocumentationLoader
from src.online_documentation_loader import OnlineDocumentationLoader


def embedding():
    documents_path = "documents"
    documents_paths = list(Path(documents_path).glob("*.html"))

    loader = FileDocumentationLoader(documents_paths)
    indexer = DocumentIndexer()

    indexer.index_documents(loader)

if __name__ == '__main__':
    # embedding()
    print(len(OnlineDocumentationLoader().load()))