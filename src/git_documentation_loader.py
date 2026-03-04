import re
from typing import Iterable, List

from langchain_core.documents import Document

from src.base_documentation_loader import BaseDocumentationLoader
import requests
import zipfile
import io
from rich import print

class GitDocumentationLoader(BaseDocumentationLoader):
    def __init__(self, base_url = "https://api.github.com/repos/godotengine/godot-docs/zipball/master", verbose=False):
        super().__init__(verbose)
        self.base_url = base_url
        self.chapters = ["tutorials", "about", "classes"]

    def _is_allow_chapter(self, filepath: str) -> bool:
        return filepath.split("/")[1] in self.chapters

    @staticmethod
    def _is_allow_file(file: str) -> bool:
        return file.endswith(".rst") and not file.endswith("index.rst")

    def _get_html_sources(self) -> Iterable[str]:
        response = requests.get(self.base_url)
        response.raise_for_status()

        zip_bytes = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_bytes) as z:
            for file in z.namelist():
                if self._is_allow_chapter(file) and self._is_allow_file(file):
                    yield f'{file}\n{z.read(file).decode("utf-8")}'

    @staticmethod
    def _is_underline(line : str):
        return bool(re.match(r"^[=\-~^`:#\"*+]+$", line.strip()))

    @staticmethod
    def _normalize_path(filepath: str) -> str:
        parts = filepath.split("/")
        return "/".join(parts[1:])

    def _build_public_url(self, filepath: str) -> str:
        normalized = self._normalize_path(filepath)
        html_path = normalized.replace(".rst", ".html")
        return f"https://docs.godotengine.org/en/stable/{html_path}"

    def _create_documents(self, rst_raw: str) -> List[Document]:
        filepath, content = rst_raw.split("\n", 1)

        lines = content.splitlines()

        doc_title = None
        sections = []
        current_section = {"title": None, "content": [], "has_code": False}

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect title (line followed by ===== or ----- etc.)
            if i + 1 < len(lines) and self._is_underline(lines[i + 1]):
                if doc_title is None:
                    doc_title = line.strip()
                else:
                    if current_section["title"]:
                        sections.append(current_section)

                    current_section = {
                        "title": line.strip(),
                        "content": [],
                        "has_code": False
                    }
                i += 2
                continue

            # Detect code block
            if line.strip().startswith(".. code-block::"):
                current_section["has_code"] = True

            current_section["content"].append(line)
            i += 1

        if current_section["title"]:
            sections.append(current_section)

        documents = []

        for section in sections:
            text_content = "\n".join(section["content"]).strip()

            documents.append(
                Document(
                    page_content=f"# {doc_title}\n\n## {section['title']}\n\n{text_content}",
                    metadata={
                        "title": doc_title,
                        "url": self._build_public_url(filepath),
                        "section": section["title"],
                        "has_code": section["has_code"],
                        "preview": text_content[:100]
                    }
                )
            )

        return documents