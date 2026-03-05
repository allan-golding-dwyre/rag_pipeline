import re
from langchain_core.documents import Document
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

from src.documentation_loader.doc_parser import GodotDocParser

COLORS = ["red", "green", "yellow", "blue", "magenta", "cyan", "bright_red",
          "bright_green", "bright_yellow", "bright_blue", "bright_magenta", "bright_cyan"]

console = Console()

def pretty_print_section(title :str):
    console.rule(f"[bold red]{title}[/bold red]")

def pretty_print_doc(document: Document, index: int):
    meta = document.metadata

    # Header metadata
    console.rule(f"[bold cyan]Doc #{index}[/bold cyan]")
    for key, value in meta.items():
        label = key.replace("_", " ").capitalize()
        color = COLORS[hash(key) % len(COLORS)]
        console.print(f"[bold]{label}:[/bold] [{color}]{value}[/{color}]")
    console.print()

    # Page content : render code blocks avec syntax highlighting
    content = document.page_content
    parts = re.split(r"(```gdscript\n.*?\n```)", content, flags=re.DOTALL)

    for part in parts:
        if part.startswith("```gdscript"):
            code = re.sub(r"```gdscript\n|```$", "", part).strip()
            console.print(Syntax(code, "gdscript", theme="monokai", line_numbers=True))
        elif part.strip():
            console.print(Text(part.strip()))

    console.print()