import argparse

from src.document_indexer import DocumentIndexer
from src.file_documentation_loader import FileDocumentationLoader
from src.online_documentation_loader import OnlineDocumentationLoader
# from rich import print

def main():
    if args.source == "file":
        documents_paths = list(Path(args.path).glob("*.html"))
        loader = FileDocumentationLoader(documents_paths, verbose=args.verbose)
    else:
        loader = OnlineDocumentationLoader(base_url=args.base_url, verbose=args.verbose)

    # --- Indexing ---
    indexer = DocumentIndexer()
    indexer.index_documents(loader)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Index Godot documentation (online or local files)"
    )

    parser.add_argument(
        "--source",
        choices=["online", "file"],
        default="online",
        help="Source of documentation (default: online)"
    )

    parser.add_argument(
        "--path",
        type=str,
        default="documents",
        help="Path to local HTML files (required if source=file)"
    )

    parser.add_argument(
        "--base-url",
        type=str,
        default="https://docs.godotengine.org/en/stable/index.html",
        help="Base URL for online documentation"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose mode"
    )

    args = parser.parse_args()
    main()