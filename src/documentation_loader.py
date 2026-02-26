from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class DocumentationLoader(BaseLoader):
    def __init__(self, paths : List[Path], verbose=False):
        self.paths = paths
        self.verbose = verbose

    def load(self) -> List[Document]:
        """Load the documentation for each file."""
        documents = []
        for filepath in self.paths:
            documents.extend(self._create_documents(filepath))
        return documents

    def _create_documents(self, filepath : Path) -> List[Document]:
        html = filepath.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find("div", itemprop="articleBody")
        doc_title = soup.find("meta", property="og:title")["content"]
        doc_url = soup.find("meta", property="og:url")["content"]

        if article is None:
            return []

        for tag in article(["script", "style"]):
            tag.decompose()

        if self.verbose:
            print("==================================================")
            print(doc_title)

        sections = self.detect_sections(article)
        documents = []

        for section in sections:
            documents.append(
                Document(
                    page_content= f"# {doc_title}\n\n ## {section['title']}\n\n{section['content']}",
                    metadata = {
                        "title": doc_title,
                        "url": doc_url,
                        "source": str(filepath),
                        "section" : section["title"],
                        "has_code": section["has_code"],
                        "preview": section["content"][:100]
                    }
                )
            )
            if self.verbose:
                print(section["title"] + f" (has code : {section["has_code"]})")
                print(section["content"])
                print("-------------------------------------------------")

        return documents

    @staticmethod
    def detect_sections(article: BeautifulSoup):
        sections = []

        top_sections = article.find_all("section", recursive=False)

        for sec in top_sections:
            h2 = sec.find("h2")
            if not h2:
                continue

            title = h2.get_text(strip=True)
            content_parts = []
            has_code = False

            for element in sec.descendants:

                # --- CODE BLOCKS ---
                if element.name == "pre":
                    parent_tabs = element.find_parent(class_="sphinx-tabs")
                    if parent_tabs:
                        tab = element.find_parent(attrs={"data-tab": True})
                        if tab and tab.get("data-tab") != "GDScript":
                            continue

                    has_code = True
                    code = element.get_text()
                    content_parts.append(f"\n### GDScript Code Example\n```gdscript\n{code}\n```\n")

                # --- LISTES ---
                elif element.name in ["ul", "ol"]:
                    items = [li.get_text(" ", strip=True) for li in element.find_all("li", recursive=False)]
                    content_parts.append("\n".join(f"- {i}" for i in items))

                # --- PARAGRAPHES ---
                elif element.name == "p":
                    if element.find_parent(["li", "pre"]) or element.find_parent("div", class_="admonition"):
                        continue
                    text = element.get_text(" ", strip=True)
                    if text:
                        content_parts.append(text)

                # --- ADMONITIONS ---
                elif element.name == "div" and "admonition" in element.get("class", []):
                    kind = element.get("class")[1] if len(element.get("class")) > 1 else "note"
                    text = element.get_text(" ", strip=True)
                    content_parts.append(f"\n[{kind.upper()}]\n{text}\n")

            if content_parts:
                sections.append({
                    "title": title,
                    "content": "\n\n".join(content_parts),
                    "has_code": has_code
                })

        return sections