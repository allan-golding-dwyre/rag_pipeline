
# https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-html-master.zip


from pathlib import Path
from typing import List, Iterable

from src.base_documentation_loader import BaseDocumentationLoader
import requests
import zipfile
import io
from rich import print


class FileFetchDocumentationLoader(BaseDocumentationLoader):
    """
    Comparer à FileDocumentationLoader et OnlineDocumentationLoader, ceci permet la récupération de la documentation stable, en mélangeant les meilleurs des deux mondes (file and online)
    On télécharge le zip de la version stable de godot, donc une seule requete (pas des centaines comme pour OnlineLoader) et puis une fois fait, on traite les fichiers html avec la même granularité possible que avec FileLoader
    """

    def __init__(self, base_url = "https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-html-stable.zip", verbose=False):
        super().__init__(verbose)
        self.base_url = base_url
        self.chapters = ["tutorials", "about", "classes"]

    def _is_allow_chapter(self, filepath: str) -> bool:
        parts = filepath.split("/")
        if len(parts) < 2:
            return True
        return parts[0] in self.chapters

    @staticmethod
    def _is_file_allowed(filepath: str) -> bool:
        return filepath.endswith(".html") and filepath.split("/")[-1] not in ["search.html", "404.html", "genindex.html"]

    def _get_html_sources(self) -> Iterable[str]:
        response = requests.get(self.base_url)
        response.raise_for_status()

        zip_bytes = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_bytes) as z:
            for file in z.namelist():
                if self._is_allow_chapter(file) and self._is_file_allowed(file):
                    print(f'\r\033[K{file}', end='', flush=True)
                    yield f'{file}\n{z.read(file).decode("utf-8")}'
