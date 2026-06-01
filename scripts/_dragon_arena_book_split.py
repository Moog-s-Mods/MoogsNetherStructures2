"""Split dragon_arena NBTs into two MC-version tiers so books load on the
whole 1.21.x range:

  - top-level  ← 1.21.0-1.21.4 shape (DataVersion 3953; each page's `raw`
                  value JSON-encoded as a string literal so the strict
                  Component codec accepts it)
  - v1_21_5/   ← 1.21.5+ shape (current 1.21.10 save; bare-string page
                  values are accepted by the lenient codec)

Filterable key is `raw` on BOTH sides — there is no key rename across the
1.21.x line. The previous version of this script renamed `raw`->`text`,
which is wrong and breaks books on 1.21-1.21.4.

Operates on every .nbt file directly under
src/main/resources/data/mns/structure/dragon_arena/. Idempotent.
"""

import json
import os
import shutil
import sys

import nbtlib
from nbtlib.tag import Compound, Int, List, String

REPO = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2"
SRC_DIR = os.path.join(
    REPO, "src", "main", "resources", "data", "mns", "structure", "dragon_arena"
)
V1_21_5_DIR = os.path.join(SRC_DIR, "v1_21_5")

DATAVERSION_1_21_0 = 3953


def load(path):
    return nbtlib.load(path)


def save(nbt, path):
    nbt.save(path, gzipped=True, byteorder="big")


def root_of(nbt):
    return nbt.root if hasattr(nbt, "root") else nbt


def json_encode_pages(node, counter):
    """For every Filterable Compound in written_book_content.pages, JSON-encode
    its `raw` value if it isn't already a quoted JSON literal."""
    if isinstance(node, Compound):
        if "minecraft:written_book_content" in node:
            wbc = node["minecraft:written_book_content"]
            pages = wbc.get("pages")
            if isinstance(pages, List):
                for p in pages:
                    if isinstance(p, Compound) and "raw" in p:
                        cur = str(p["raw"])
                        if not (cur.startswith('"') and cur.endswith('"')):
                            p["raw"] = String(json.dumps(cur))
                            counter[0] += 1
        for v in node.values():
            json_encode_pages(v, counter)
    elif isinstance(node, List):
        for item in node:
            json_encode_pages(item, counter)


def process(file_name):
    top = os.path.join(SRC_DIR, file_name)
    mirror = os.path.join(V1_21_5_DIR, file_name)

    # 1) Mirror current top-level to v1_21_5/ (1.21.5+ shape: bare strings)
    os.makedirs(V1_21_5_DIR, exist_ok=True)
    shutil.copyfile(top, mirror)

    # 2) Downgrade top-level: lower DataVersion, JSON-encode page raw values
    nbt = load(top)
    root = root_of(nbt)
    old_dv = root.get("DataVersion")
    root["DataVersion"] = Int(DATAVERSION_1_21_0)
    counter = [0]
    json_encode_pages(root, counter)
    save(nbt, top)

    print(
        f"{file_name:<18}  DataVersion {old_dv} -> {DATAVERSION_1_21_0}, "
        f"JSON-encoded {counter[0]} page(s)"
    )


def main():
    files = sorted(
        f for f in os.listdir(SRC_DIR)
        if f.endswith(".nbt") and os.path.isfile(os.path.join(SRC_DIR, f))
    )
    if not files:
        print("no .nbt files at top level")
        return 1
    for f in files:
        process(f)
    print(f"\nprocessed {len(files)} NBTs -> top-level (1.21.0-1.21.4) + v1_21_5/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
