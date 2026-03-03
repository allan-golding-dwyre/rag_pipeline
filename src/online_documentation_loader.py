import time
from typing import Iterable

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin, urldefrag

from src import config
from tqdm import tqdm
from src.base_documentation_loader import BaseDocumentationLoader
from concurrent.futures import ThreadPoolExecutor, as_completed

class OnlineDocumentationLoader(BaseDocumentationLoader):
    def __init__(self, base_url = "https://docs.godotengine.org/en/stable/index.html", verbose=False):
        super().__init__(verbose)
        self.base_url = base_url
        self.session = requests.Session()
        self.headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"
        }

        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.max_workers = 10

    def fetch(self, url: str):
        time.sleep(0.5)
        response = self.session.get(url, timeout=10, headers=self.headers)
        response.raise_for_status()
        return response.content

    def _get_html_sources(self) -> Iterable[str]:
        print("Getting HTML sources...")
        urls = self._get_chapter_urls()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.fetch, url) for url in urls]
            progress_bar = tqdm(as_completed(futures),total=len(futures), desc="Parsing pages", unit="page")
            for future in progress_bar:
                yield future.result()

        self.session.close()

    def _get_chapter_urls(self):
        response = requests.get(self.base_url, headers=self.headers)
        if response.status_code == 429:
            raise Exception("Too Many Requests")

        soup = BeautifulSoup(response.content, "lxml")
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
