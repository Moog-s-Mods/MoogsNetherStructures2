"""Downgrade two MNS structure NBTs from MC 1.21.5+ Filterable shape (raw key)
to MC 1.21.0-1.21.4 Filterable shape (text key), and apply Page=0 to lecterns.

Layout:
- v1_21_5/<path>  ← exact copy of current top-level (1.21.5+ shape, raw key)
- top-level <path> ← downgraded version (raw->text in title/pages, DataVersion 3953)
- v1_21_9/<path>  ← in-place Page=0 edit only (lectern piece only)
"""
import gzip
import io
import shutil
import os
import sys

import nbtlib
from nbtlib.tag import Compound, List, Int, String

REPO = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2"
STRUCT = os.path.join(REPO, "src", "main", "resources", "data", "mns", "structure", "mega_fortress")

PIECES = [
    # (relative path under mega_fortress/, has_lectern)
    ("forks/roofless_fork_side_2_6.nbt", False),
    ("start/mega_crossing_north_straight_1.nbt", True),
]


def load(path):
    return nbtlib.load(path)


def save(nbt, path):
    # nbtlib preserves gzipped flag from load; explicitly use gzipped for structure NBTs
    nbt.save(path, gzipped=True, byteorder='big')


def is_filterable_in_book_content(parent_path):
    """Path like ['components', 'minecraft:written_book_content', 'title']
       or ['components', 'minecraft:written_book_content', 'pages', '<idx>']."""
    if len(parent_path) < 3:
        return False
    if parent_path[-3] != "components":
        return False
    if parent_path[-2] != "minecraft:written_book_content":
        return False
    last = parent_path[-1]
    if last == "title":
        return True
    # pages list item: path ends ['components', 'written_book_content', 'pages', <int>]
    if len(parent_path) >= 4 and parent_path[-2] == "pages":
        # parent_path[-1] is the list index (int as string in our walker)
        return True
    return False


def rewrite_filterables(node, path):
    """Walk the NBT tree; rename 'raw' -> 'text' in any Compound that is a Filterable
    inside written_book_content."""
    if isinstance(node, Compound):
        # Decide whether THIS compound is a Filterable wrapper for written_book_content
        is_title_filterable = (
            len(path) >= 2
            and path[-1] == "title"
            and path[-2] == "minecraft:written_book_content"
        )
        is_page_filterable = (
            len(path) >= 3
            and path[-3] == "minecraft:written_book_content"
            and path[-2] == "pages"
            # path[-1] is the int list index
        )
        if (is_title_filterable or is_page_filterable) and "raw" in node:
            val = node.pop("raw")
            node["text"] = val
        # Recurse
        for k, v in list(node.items()):
            rewrite_filterables(v, path + [k])
    elif isinstance(node, List):
        for i, item in enumerate(node):
            rewrite_filterables(item, path + [i])


def find_lecterns_set_page_zero(root):
    """Set BE Page=0 on every lectern block-entity in the structure."""
    blocks = root.get("blocks", [])
    count = 0
    for b in blocks:
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


def root_of(nbt):
    return nbt.root if hasattr(nbt, "root") else nbt


def process_piece(rel, has_lectern):
    top = os.path.join(STRUCT, rel)
    v1_21_5 = os.path.join(STRUCT, "v1_21_5", rel)
    v1_21_9 = os.path.join(STRUCT, "v1_21_9", rel)

    print(f"\n=== {rel} ===")
    print(f"  top-level:  {top}")
    print(f"  v1_21_5:    {v1_21_5}")
    print(f"  v1_21_9:    {v1_21_9}")

    if not os.path.exists(top):
        print(f"  ! MISSING top-level NBT, aborting this piece")
        return False

    # 1) Copy current top-level (1.21.5+ shape) to v1_21_5/<rel>
    os.makedirs(os.path.dirname(v1_21_5), exist_ok=True)
    shutil.copyfile(top, v1_21_5)
    print(f"  copied top-level -> v1_21_5/")

    # 2a) For lectern piece, set Page=0 in the v1_21_5 copy
    if has_lectern:
        nbt = load(v1_21_5)
        r = root_of(nbt)
        n = find_lecterns_set_page_zero(r)
        save(nbt, v1_21_5)
        print(f"  v1_21_5: set Page=0 on {n} lectern(s)")

    # 2b) For lectern piece, also set Page=0 in v1_21_9 IN PLACE
    if has_lectern:
        if os.path.exists(v1_21_9):
            nbt = load(v1_21_9)
            r = root_of(nbt)
            n = find_lecterns_set_page_zero(r)
            save(nbt, v1_21_9)
            print(f"  v1_21_9: set Page=0 on {n} lectern(s)")
        else:
            print(f"  ! v1_21_9 missing — skipping Page edit there")

    # 3) Downgrade top-level: rename raw->text in book content Filterables, set DataVersion=3953
    nbt = load(top)
    r = root_of(nbt)

    # Rewrite Filterables inside written_book_content (both entity items and block-entity Book)
    rewrite_filterables(r, [])

    # Lower DataVersion
    old_dv = r.get("DataVersion")
    r["DataVersion"] = Int(3953)

    # Page=0 on lectern in the downgraded top-level too
    n_pg = 0
    if has_lectern:
        n_pg = find_lecterns_set_page_zero(r)

    save(nbt, top)
    print(f"  top-level: downgraded (DataVersion {old_dv} -> 3953, raw->text rename, Page=0 on {n_pg} lectern(s))")
    return True


def verify():
    print("\n=== Verification (read-back) ===")
    for rel, has_lectern in PIECES:
        for variant_root, label, expect_key, expect_dv in [
            (STRUCT, "top-level (1.21.0-1.21.4 shape)", "text", 3953),
            (os.path.join(STRUCT, "v1_21_5"), "v1_21_5 (1.21.5+ shape)", "raw", 4556),
            (os.path.join(STRUCT, "v1_21_9"), "v1_21_9 (1.21.9+ shape)", "raw", 4556),
        ]:
            p = os.path.join(variant_root, rel)
            if not os.path.exists(p):
                print(f"  ! MISSING: {p}")
                continue
            nbt = load(p)
            r = root_of(nbt)
            dv = int(r.get("DataVersion"))
            # Find a Filterable to inspect
            found_key = "?"
            # Walk entities and blocks for the first written_book_content
            def find_first_filterable(node):
                if isinstance(node, Compound):
                    if "minecraft:written_book_content" in node:
                        wbc = node["minecraft:written_book_content"]
                        title = wbc.get("title")
                        if isinstance(title, Compound):
                            if "raw" in title: return "raw"
                            if "text" in title: return "text"
                        pages = wbc.get("pages")
                        if isinstance(pages, List) and pages:
                            first = pages[0]
                            if isinstance(first, Compound):
                                if "raw" in first: return "raw"
                                if "text" in first: return "text"
                    for v in node.values():
                        x = find_first_filterable(v)
                        if x: return x
                elif isinstance(node, List):
                    for item in node:
                        x = find_first_filterable(item)
                        if x: return x
                return None
            found_key = find_first_filterable(r) or "?"
            # Lectern Page check
            page = None
            if has_lectern:
                for b in r.get("blocks", []):
                    if isinstance(b, Compound):
                        be = b.get("nbt")
                        if be is not None and str(be.get("id", "")) == "minecraft:lectern":
                            page = int(be.get("Page", -1))
                            break
            ok_dv = (dv == expect_dv)
            ok_key = (found_key == expect_key)
            ok_page = (page == 0) if has_lectern else True
            tag = "OK" if (ok_dv and ok_key and ok_page) else "FAIL"
            print(f"  [{tag}] {label}: DataVersion={dv} (expect {expect_dv}); Filterable key={found_key} (expect {expect_key}); Page={page} (expect 0 if lectern)")


if __name__ == "__main__":
    all_ok = True
    for rel, has_lectern in PIECES:
        ok = process_piece(rel, has_lectern)
        all_ok = all_ok and ok
    verify()
    sys.exit(0 if all_ok else 1)
