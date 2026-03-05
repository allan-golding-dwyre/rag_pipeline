from __future__ import annotations

from typing import List, Optional
from rich import print
from bs4 import BeautifulSoup, Tag, NavigableString
from langchain_core.documents import Document
import base64

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def remove_non_ascii(text: str) -> str:
    return text.encode('ascii', 'ignore').decode('ascii')

def _text(tag: Tag, sep: str = " ") -> str:
    if not tag:
        return ""

    def _render_node(node) -> str:
        if isinstance(node, NavigableString):
            return remove_non_ascii(str(node))

        if node.name == "a":
            href = node.get("href", "")
            title = node.get_text(strip=True)
            title = remove_non_ascii(title)
            if href and title:
                return f"[{title}]({href})"
            return title

        if node.name in ("strong", "b"):
            inner = "".join(_render_node(child) for child in node.children)
            return f"**{inner.strip()}**"

        if node.name in ("em", "i"):
            inner = "".join(_render_node(child) for child in node.children)
            return f"*{inner.strip()}*"

        if node.name == "code":
            return f"`{node.get_text()}`"

        # Pour tous les autres tags, on descend recursivement
        children_text = "".join(_render_node(child) for child in node.children)
        if node.name in ("p", "li", "br", "div"):
            return children_text + sep
        return children_text

    result = "".join(_render_node(child) for child in tag.children)
    # Nettoyage des espaces multiples
    result = " ".join(result.split())
    return result.strip()

def _table_to_markdown(table: Tag) -> str:
    """Convert an HTML table to a Markdown table string."""
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["th", "td"])]
        if any(cells):
            rows.append(cells)

    if not rows:
        return ""

    # Normalise column count
    col_count = max(len(r) for r in rows)
    for r in rows:
        while len(r) < col_count:
            r.append("")

    def md_row(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    lines = [md_row(rows[0]), "| " + " | ".join(["---"] * col_count) + " |"]
    for row in rows[1:]:
        lines.append(md_row(row))

    return "\n".join(lines)

def _has_code(tag: Tag) -> bool:
    return bool(tag.find("pre"))

def _extract_code_blocks(tag: Tag) -> list[str]:
    blocks = []
    for pre in tag.find_all("pre"):
        parent_tabs = pre.find_parent(class_="sphinx-tabs")
        if parent_tabs:
            # Le panel contient name= en base64, pas data-tab
            panel = pre.find_parent(class_="sphinx-tabs-panel")
            if panel:
                raw_name = panel.get("name", "")
                try:
                    decoded = base64.b64decode(raw_name).decode("utf-8")
                except Exception:
                    decoded = ""
                if decoded != "GDScript":
                    continue  # ← skip C#, Visual Script, etc.

        code = pre.get_text()
        blocks.append(f"```gdscript\n{code}\n```")
    return blocks

def extract_admonition(tag: Tag) -> str:
    kind = tag.get("class")[1] if len(tag.get("class")) > 1 else "note"
    kind = remove_non_ascii(kind)
    text = _text(tag)
    return f"\n[{kind.upper()}]\n{text}\n"

# ---------------------------------------------------------------------------


class GodotDocParser:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    # ------------------------------------------------------------------
    def create_documents(self, html: str) -> List[Document]:
        soup = BeautifulSoup(html, "lxml")

        article = soup.find("div", itemprop="articleBody")
        title = soup.find("meta", property="og:title")["content"]
        doc_url = soup.find("meta", property="og:url")["content"]

        if article is None:
            return []

        for tag in article(["script", "style"]):
            tag.decompose()

        if self.verbose:
            print("=" * 60)
            print(title)

        return self._parse(article, title, doc_url)

    def _parse(self, article, title, doc_url) -> List[Document]:
        if "/classes/class_" in doc_url:
            return self._parse_class_page(article, title, doc_url)
        else:
            return self._parse_concept_page(article, title, doc_url)

    # -----------------------------------------------------------------------
    # Parser : pages conceptuelles
    # -----------------------------------------------------------------------

    def _parse_concept_page(self, article, title, doc_url) -> List[Document]:
        documents = []

        root_section = article.find("section", recursive=False)
        if not root_section:
            return []

        # --- Intro : contenu avant le premier h2 ---
        intro_parts = [f"# {title}"]
        for child in root_section.children:
            if not isinstance(child, Tag):
                continue
            if child.name in ("h1", "span"):
                continue
            if child.name == "section":
                break
            md = self._to_markdown(child)
            if md:
                intro_parts.append(md)

        if len(intro_parts) > 1:
            documents.append(self._make_document(
                content="\n\n".join(intro_parts),
                doc_type="concept",
                section=title,
                source=doc_url,
                title=title,
            ))

        # --- 1 Document par sous-section h2 ---
        for sub_section in root_section.find_all("section", recursive=False):
            h2 = sub_section.find("h2")
            if not h2:
                continue

            section_title = _text(h2)
            parts = [f"# {title}\n\n## {section_title}"]

            for child in sub_section.children:
                if not isinstance(child, Tag) or child.name == "h2":
                    continue
                md = self._to_markdown(child)
                if md:
                    parts.append(md)

            documents.append(self._make_document(
                content="\n\n".join(parts),
                doc_type="concept",
                section=section_title,
                source=doc_url,
                title=title,
            ))

        return documents

    # -----------------------------------------------------------------------
    # Parser : pages de classes
    # -----------------------------------------------------------------------

    def _parse_class_page(self, article: Tag, title: str, doc_url: str) -> List[Document]:
        documents = []
        class_name = title.replace(" — Godot Engine documentation", "").strip()

        # --- 1. Description générale + sections d'intro (description, tutorials) ---
        header_parts = [f"# {class_name}"]

        root_section = article.find("section", recursive=False)
        if not root_section:
            return []

        # Brief description avant les sous-sections
        for child in root_section.children:
            if not isinstance(child, Tag):
                continue
            if child.name == "section":
                break
            md = self._to_markdown(child)
            if md:
                header_parts.append(md)

        # Sections d'intro : description, tutorials
        for sub in root_section.find_all("section", recursive=False):
            sub_id = sub.get("id", "")
            if sub_id in ("description", "tutorials"):
                h2 = sub.find("h2")
                if h2:
                    header_parts.append(f"## {_text(h2)}")
                for child in sub.children:
                    if not isinstance(child, Tag) or child.name == "h2":
                        continue
                    md = self._to_markdown(child)
                    if md:
                        header_parts.append(md)

        documents.append(self._make_document(
            content="\n\n".join(header_parts),
            doc_type="class_description",
            section="description",
            source=doc_url,
            title=title,
            class_name=class_name,
        ))

        # --- 2. Sections de résumé (tables) ---
        for section in root_section.find_all("section", recursive=False):
            section_id = section.get("id", "")

            if section_id in ("description", "tutorials"):
                continue

            # Détection par classe CSS Godot
            classes = section.get("class", [])

            if "classref-reftable-group" in classes:
                # Résumé tabulaire
                table = section.find("table")
                if table:
                    content = f"## {class_name} – {section_id}\n\n{_table_to_markdown(table)}"
                    documents.append(self._make_document(
                        content=content,
                        doc_type="class_summary",
                        section=section_id,
                        source=doc_url,
                        title=title,
                        class_name=class_name,
                    ))

            elif "classref-descriptions-group" in classes:
                # Descriptions détaillées : dl ou flat
                kind = section_id.replace("-descriptions", "")
                dls = section.find_all("dl", recursive=False)
                if dls:
                    for dl in dls:
                        doc = self._dl_to_document(dl, class_name, kind, title, doc_url)
                        if doc:
                            documents.append(doc)
                else:
                    docs = self._parse_flat_descriptions(
                        section, class_name, kind, title, doc_url
                    )
                    documents.extend(docs)

        return documents

    def _parse_flat_descriptions(self, section, class_name, kind, title, doc_url) -> list[Document]:
        documents = []
        current_parts: list[str] = []
        current_name: str = ""

        ENTRY_CLASSES = {
            "classref-annotation", "classref-constant", "classref-method",
            "classref-signal", "classref-enumeration", "classref-enumeration-constant",
            "classref-property",
        }

        def flush():
            if not current_parts:
                return
            documents.append(self._make_document(
                content="\n\n".join(current_parts),
                doc_type=f"class_{kind}",
                section=kind,
                source=doc_url,
                title=title,
                class_name=class_name,
                member_name=current_name,
            ))
            current_parts.clear()

        for child in section.children:
            if not isinstance(child, Tag):
                continue

            if child.name == "hr" and "classref-item-separator" in child.get("class", []):
                flush()
                current_name = ""
                continue

            if child.name == "p" and ENTRY_CLASSES & set(child.get("class", [])):
                sig = _text(child)
                current_name = child.get("id", sig)
                current_parts.append(f"### `{sig}`")
                continue

            md = self._to_markdown(child)
            if md:
                current_parts.append(md)

        flush()
        return documents

    def _dl_to_document(self, dl, class_name, kind, title, doc_url) -> Optional[Document]:
        parts: list[str] = []

        dt = dl.find("dt")
        if dt:
            sig = _text(dt)
            parts.append(f"### `{sig}`")

        dd = dl.find("dd")
        if dd:
            for child in dd.children:
                if not isinstance(child, Tag):
                    continue
                md = self._to_markdown(child)
                if md:
                    parts.append(md)

        if not parts:
            return None

        name = dt.get("id", sig if dt else "unknown") if dt else "unknown"

        return self._make_document(
            content="\n\n".join(parts),
            doc_type=f"class_{kind}",
            source=doc_url,
            title=title,
            class_name=class_name,
            member_name=name,
        )

    def _to_markdown(self, tag: Tag) -> str:
        """Convertit un tag HTML en Markdown de façon générique."""
        if not isinstance(tag, Tag):
            return ""

        name = tag.name
        classes = tag.get("class", [])

        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return f"{'#' * int(name[1])} {_text(tag)}"

        if name == "p":
            t = _text(tag)
            return t if t else ""

        if name in ("ul", "ol"):
            items = [f"- {_text(li)}" for li in tag.find_all("li", recursive=False)]
            return "\n".join(items)

        if name == "table":
            return _table_to_markdown(tag)

        if name == "blockquote":
            t = _text(tag)
            return "\n".join(f"> {line}" for line in t.splitlines()) if t else ""

        if "admonition" in classes:
            return extract_admonition(tag)

        if name == "hr":
            return ""

        # Conteneur avec code GDScript (sphinx-tabs, div highlight, etc.)
        if _has_code(tag):
            blocks = _extract_code_blocks(tag)
            return "\n\n".join(blocks) if blocks else ""

        # Fallback : descendre dans les enfants
        parts = []
        for child in tag.children:
            if not isinstance(child, Tag):
                continue
            md = self._to_markdown(child)
            if md:
                parts.append(md)
        return "\n\n".join(parts)

    @staticmethod
    def _make_document(
            content: str,
            doc_type: str,
            source: str,
            title: str,
            *,
            section: str = "",
            class_name: str = "",
            member_name: str = "",
    ) -> Document:
        has_code = "```" in content

        return Document(
            page_content=content,
            metadata={
                "source": source,
                "title": title,
                "type": doc_type,
                "section": section,
                "class_name": class_name,
                "member_name": member_name,
                "has_code": has_code,
            }
        )