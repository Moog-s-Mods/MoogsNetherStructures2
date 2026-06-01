"""Downgrade two MNS mega_fortress structure NBTs so their books load on
1.21.0-1.21.4.

The Filterable codec field name is `raw` across the entire 1.21.x range —
the previous version of this script renamed `raw`->`text`, which was wrong
and broke books on 1.21-1.21.4. The actual differences between 1.21.5+ and
1.21.0-1.21.4 for `written_book_content` are:

  1. DataVersion must be <= the target MC's DV (DFU is forward-only; structures
     with a higher source DV are refused). We lower to 3953 (1.21.0) to cover
     the whole 1.21.0-1.21.4 range.
  2. Each page's `raw` value must be a JSON-encoded string literal — e.g.
     `"\"Hello\\n\\nworld\""`. The 1.21.5+ Component codec accepts a bare NBT
     String as literal text; the 1.21.0-1.21.4 codec parses pages as strict
     JSON and rejects multi-line bare strings.
  3. Title is fine as a bare NBT String on both sides (different codec path
     than pages).

Layout produced:
  - top-level <path>   ← downgraded (DataVersion 3953, pages JSON-encoded,
                          Page=0 on lectern)
  - v1_21_5/<path>     ← exact copy of the source (1.21.5+ shape, bare-string
                          pages, original DataVersion, Page=0 applied for the
                          lectern piece)
  - v1_21_9/<path>     ← in-place Page=0 edit only (lectern piece only)

Idempotent: a page already starting+ending with `"` is left alone.
"""
import json
import os
import shutil
import sys

import nbtlib
from nbtlib.tag import Compound, Int, List, String

REPO = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2"
STRUCT = os.path.join(
    REPO, "src", "main", "resources", "data", "mns", "structure", "mega_fortress"
)

PIECES = [
    # (relative path under mega_fortress/, has_lectern)
    ("forks/roofless_fork_side_2_6.nbt", False),
    ("start/mega_crossing_north_straight_1.nbt", True),
]

DATAVERSION_1_21_0 = 3953


def load(path):
    return nbtlib.load(path)


def save(nbt, path):
    nbt.save(path, gzipped=True, byteorder="big")


def root_of(nbt):
    return nbt.root if hasattr(nbt, "root") else nbt


def json_encode_pages(node, counter):
    """Walk the NBT tree; for every Filterable Compound in
    written_book_content.pages, JSON-encode its `raw` value if not already."""
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


def set_lectern_page_zero(root):
    count = 0
    for b in root.get("blocks", []):
        if not isinstance(b, Compound):
            continue
        be = b.get("nbt")
        if be is None:
            continue
        if str(be.get("id", "")) != "minecraft:lectern":
            continue
        be["Page"] = Int(0)
        count += 1
    return count


def process_piece(rel, has_lectern):
    top = os.path.join(STRUCT, rel)
    v1_21_5 = os.path.join(STRUCT, "v1_21_5", rel)
    v1_21_9 = os.path.join(STRUCT, "v1_21_9", rel)

    print(f"\n=== {rel} ===")

    if not os.path.exists(top):
        print(f"  ! MISSING top-level NBT, aborting this piece")
        return False

    # 1) Copy current top-level (1.21.5+ shape) to v1_21_5/<rel>
    os.makedirs(os.path.dirname(v1_21_5), exist_ok=True)
    shutil.copyfile(top, v1_21_5)
    print(f"  copied top-level -> v1_21_5/")

    # 2a) Page=0 in the v1_21_5 mirror for lecterns
    if has_lectern:
        nbt = load(v1_21_5)
        r = root_of(nbt)
        n = set_lectern_page_zero(r)
        save(nbt, v1_21_5)
        print(f"  v1_21_5: set Page=0 on {n} lectern(s)")

    # 2b) Page=0 in v1_21_9 in place (lectern piece only)
    if has_lectern and os.path.exists(v1_21_9):
        nbt = load(v1_21_9)
        r = root_of(nbt)
        n = set_lectern_page_zero(r)
        save(nbt, v1_21_9)
        print(f"  v1_21_9: set Page=0 on {n} lectern(s)")

    # 3) Downgrade top-level: lower DataVersion, JSON-encode page raw values
    nbt = load(top)
    r = root_of(nbt)
    old_dv = r.get("DataVersion")
    r["DataVersion"] = Int(DATAVERSION_1_21_0)
    counter = [0]
    json_encode_pages(r, counter)
    n_pg = set_lectern_page_zero(r) if has_lectern else 0
    save(nbt, top)
    print(
        f"  top-level: DataVersion {old_dv} -> {DATAVERSION_1_21_0}, "
        f"JSON-encoded {counter[0]} page(s), Page=0 on {n_pg} lectern(s)"
    )
    return True


def verify():
    print("\n=== Verification ===")
    for rel, has_lectern in PIECES:
        for variant_root, label, expect_dv in [
            (STRUCT, "top-level (1.21.0-1.21.4)", DATAVERSION_1_21_0),
            (os.path.join(STRUCT, "v1_21_5"), "v1_21_5 (1.21.5+)", None),
            (os.path.join(STRUCT, "v1_21_9"), "v1_21_9 (1.21.9+)", None),
        ]:
            p = os.path.join(variant_root, rel)
            if not os.path.exists(p):
                print(f"  ! MISSING: {p}")
                continue
            nbt = load(p)
            r = root_of(nbt)
            dv = int(r.get("DataVersion"))
            # Check pages encoding by sampling first page
            page_shape = "?"
            def find_first_page(node):
                if isinstance(node, Compound):
                    if "minecraft:written_book_content" in node:
                        wbc = node["minecraft:written_book_content"]
                        pages = wbc.get("pages")
                        if isinstance(pages, List) and pages:
                            first = pages[0]
                            if isinstance(first, Compound) and "raw" in first:
                                return str(first["raw"])
                    for v in node.values():
                        x = find_first_page(v)
                        if x is not None:
                            return x
                elif isinstance(node, List):
                    for item in node:
                        x = find_first_page(item)
                        if x is not None:
                            return x
                return None
            sample = find_first_page(r)
            if sample is not None:
                page_shape = "json-encoded" if (sample.startswith('"') and sample.endswith('"')) else "bare-string"
            ok_dv = (dv == expect_dv) if expect_dv is not None else True
            print(
                f"  {label} {rel}: DV={dv}"
                + (f" (expect {expect_dv})" if expect_dv else "")
                + f", page0={page_shape}"
                + ("  [DV-FAIL]" if not ok_dv else "")
            )


if __name__ == "__main__":
    all_ok = True
    for rel, has_lectern in PIECES:
        ok = process_piece(rel, has_lectern)
        all_ok = all_ok and ok
    verify()
    sys.exit(0 if all_ok else 1)
