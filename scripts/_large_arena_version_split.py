"""Split fresh 1.21.10 large_arena NBTs into 4 MC-version tiers.

Top-level (1.21.0-1.21.3): iron_chain -> chain, resin_block -> honey_block,
  DataVersion 3953, book pages JSON-encoded (raw key preserved).
v1_21_4/ (1.21.4): iron_chain -> chain, resin_block kept, DataVersion 4189,
  book pages JSON-encoded.
v1_21_5/ (1.21.5-1.21.8): iron_chain -> chain, resin_block kept,
  DataVersion 4325, book pages bare strings (lenient codec).
v1_21_9/ (1.21.9-26.1.2): iron_chain kept, resin_block kept,
  DataVersion 4556, book pages bare strings.

Run after copying fresh 1.21.10 saves into top-level. Idempotent: pages
already JSON-encoded are left alone, palette subs only apply if matching.
"""
import json
import os
import shutil
import sys

import nbtlib
from nbtlib.tag import Compound, Int, List, String

REPO = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2"
SRC = os.path.join(
    REPO, "src", "main", "resources", "data", "mns", "structure", "large_arena"
)
PIECES = ["r1", "r2", "r3", "l1", "l2", "l3"]
BOOK_PIECES = {"r3"}

TIERS = [
    # (folder, dv, palette_subs, jsonize_book)
    (None,        3953, {"minecraft:iron_chain": "minecraft:chain",
                          "minecraft:resin_block": "minecraft:honey_block"}, True),
    ("v1_21_4",   4189, {"minecraft:iron_chain": "minecraft:chain"}, True),
    ("v1_21_5",   4325, {"minecraft:iron_chain": "minecraft:chain"}, False),
    ("v1_21_9",   4556, {}, False),
]


def load(p):
    return nbtlib.load(p)


def save(nbt, p):
    nbt.save(p, gzipped=True, byteorder="big")


def root_of(n):
    return n.root if hasattr(n, "root") else n


def substitute_palette(root, subs):
    palette = root.get("palette") or []
    n = 0
    for e in palette:
        name = str(e.get("Name", ""))
        if name in subs:
            e["Name"] = String(subs[name])
            n += 1
    return n


def json_encode_book_pages(node, counter):
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
            json_encode_book_pages(v, counter)
    elif isinstance(node, List):
        for v in node:
            json_encode_book_pages(v, counter)


def process_piece(piece):
    src = os.path.join(SRC, f"{piece}.nbt")
    print(f"\n=== {piece} ===")
    if not os.path.exists(src):
        print(f"  MISSING top-level NBT, skipping")
        return

    # Read once into memory as the canonical fresh source
    fresh_bytes = open(src, "rb").read()

    for folder, dv, subs, jsonize in TIERS:
        if folder is None:
            dst = src
        else:
            dst_dir = os.path.join(SRC, folder)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, f"{piece}.nbt")
            with open(dst, "wb") as fh:
                fh.write(fresh_bytes)

        nbt = load(dst)
        r = root_of(nbt)
        old_dv = int(r.get("DataVersion"))
        n_sub = substitute_palette(r, subs) if subs else 0
        r["DataVersion"] = Int(dv)
        n_book = 0
        if jsonize and piece in BOOK_PIECES:
            counter = [0]
            json_encode_book_pages(r, counter)
            n_book = counter[0]
        save(nbt, dst)

        label = "top-level" if folder is None else f"{folder}/"
        print(f"  {label:>10} DV {old_dv}->{dv}, {n_sub} palette sub(s), {n_book} book page JSON-encode(s)")


def main():
    for p in PIECES:
        process_piece(p)
    print("\ndone.")


if __name__ == "__main__":
    main()
