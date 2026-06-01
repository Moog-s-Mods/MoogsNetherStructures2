"""Scan all mega_fortress and dragon_arena NBTs for written_book_content
and print container/title/page shape for each."""
import os, sys, nbtlib

ROOTS = [
    r"src/main/resources/data/mns/structure/mega_fortress",
    r"src/main/resources/data/mns/structure/dragon_arena",
]

def find_books(node, path, out):
    if hasattr(node, "items"):
        if "minecraft:written_book_content" in node:
            out.append((list(path), node["minecraft:written_book_content"]))
        for k, v in node.items():
            find_books(v, path + [k], out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            find_books(v, path + [i], out)

for root_dir in ROOTS:
    for dirpath, _, files in os.walk(root_dir):
        for f in files:
            if not f.endswith(".nbt"):
                continue
            full = os.path.join(dirpath, f)
            try:
                nbt = nbtlib.load(full)
            except Exception as e:
                continue
            root = nbt.root if hasattr(nbt, "root") else nbt
            books = []
            find_books(root, [], books)
            if not books:
                continue
            rel = os.path.relpath(full, ".").replace(os.sep, "/")
            dv = root.get("DataVersion")
            for path, b in books:
                title = b.get("title")
                title_keys = list(title.keys()) if hasattr(title, "keys") else f"<{type(title).__name__}>"
                pages = b.get("pages")
                first = pages[0] if pages else None
                page_keys = list(first.keys()) if hasattr(first, "keys") else f"<{type(first).__name__}>"
                container = path[0] if path else "?"
                where = "/".join(str(x) for x in path[:5])
                print(f"{rel}  DV={dv}  title_keys={title_keys} page_keys={page_keys} where={where}")
