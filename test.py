
import requests

from src import pretty_print_doc, pretty_print_section
from src.documentation_loader.doc_parser import GodotDocParser
from rich import print

tests_urls= [
    "https://docs.godotengine.org/en/stable/tutorials/best_practices/introduction_best_practices.html",
     "https://docs.godotengine.org/en/stable/about/introduction.html",
    "https://docs.godotengine.org/en/stable/classes/class_%40gdscript.html",
    "https://docs.godotengine.org/en/stable/classes/class_aescontext.html",
    "https://docs.godotengine.org/en/stable/tutorials/animation/animation_track_types.html",
    "https://docs.godotengine.org/en/stable/about/system_requirements.html#godot-editor",
    "https://docs.godotengine.org/en/stable/classes/class_audioserver.html",
    "https://docs.godotengine.org/en/stable/classes/class_animatedsprite2d.html"
    "https://docs.godotengine.org/en/stable/about/list_of_features.html"
]

parser = GodotDocParser()
docs_size = {}
for url in tests_urls:
    html = requests.get(url).text
    docs = parser.create_documents(html)
    pretty_print_section(docs[0].metadata.get("title", "Untitled"))
    docs_size[docs[0].metadata.get("title", "Untitled")] = len(docs)
    for i, doc in enumerate(docs):
        pretty_print_doc(doc, i)

pretty_print_section("Detailed Information")
for k, v in docs_size.items():
    print(f"{k}: {v}")