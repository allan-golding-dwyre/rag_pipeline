
# https://nightly.link/godotengine/godot-docs/workflows/build_offline_docs/master/godot-docs-html-master.zip


from typing import Iterable

from stream_unzip import stream_unzip
from tqdm import tqdm

from src.documentation_loader.base_documentation_loader import BaseDocumentationLoader
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
        response = requests.get(self.base_url, stream=True)
        response.raise_for_status()

        total = int(response.headers.get("content-length", 0))

        def chunked_response():
            with tqdm(total=total, unit="B", unit_scale=True, desc="Downloading docs") as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    bar.update(len(chunk))
                    yield chunk

        for file_name, file_size, unzipped_chunks in stream_unzip(chunked_response()):
            filepath = file_name.decode('utf-8')

            if not self._is_allow_chapter(filepath) or not self._is_file_allowed(filepath):
                # Consommer les chunks quand même pour ne pas bloquer le stream
                # Car stream_unzip est un lazy génerator, donc il attend qu'on lui demande les chunks pour envoyer le reste
                for _ in unzipped_chunks:
                    pass
                continue

            content = b"".join(unzipped_chunks).decode('utf-8')
            yield content
