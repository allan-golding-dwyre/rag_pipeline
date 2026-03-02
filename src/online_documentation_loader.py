from typing import Iterable

from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urldefrag

from src import config
from src.base_documentation_loader import BaseDocumentationLoader


class OnlineDocumentationLoader(BaseDocumentationLoader):
    def __init__(self, base_url = "https://docs.godotengine.org/en/stable/index.html#", verbose=False):
        super().__init__(verbose)
        self.base_url = base_url

    def _get_html_sources(self) -> Iterable[str]:
        urls = self._get_chapter_urls()
        for url in urls:
            response = requests.get(url)
            yield response.content

    def _get_chapter_urls(self):
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.content, "html.parser")
        nav = soup.find("div", class_="wy-menu wy-menu-vertical")
        urls = set()

        captions = nav.find_all("p", class_="caption")

        for caption in captions:
            title = caption.get_text(strip=True)

            if title in config.CHAPTERS_TO_FETCH:
                ul = caption.find_next_sibling("ul")

                for link in ul.find_all("a", class_="reference internal"):
                    href = link.get("href")
                    full_url, _= urldefrag(urljoin(self.base_url, href))
                    urls.add(full_url)
        return list(urls)
