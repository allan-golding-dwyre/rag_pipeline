from pathlib import Path
from typing import List, Iterable

from src.base_documentation_loader import BaseDocumentationLoader


class FileDocumentationLoader(BaseDocumentationLoader):
    def __init__(self, directory: str , verbose=False):
        super().__init__(verbose)
        self.paths = list(Path(directory).glob("*.html"))

    def _get_html_sources(self) -> Iterable[str]:
        for path in self.paths:
            yield path.read_text(encoding="utf-8")