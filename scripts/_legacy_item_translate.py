"""Translate the 5 affected MNS 1.20-datapack NBTs into legacy-tag ItemStack shape
for MC 1.20.0-1.20.4, while preserving the existing components shape under v1_20_5/
for MC 1.20.5-1.20.6.

Per piece:
  v1_20_5/<rel>  <- exact copy of current top-level (1.20.5+ shape, untouched)
  top-level <rel> <- translated copy (DataVersion 3465, ItemStack uses tag.* + Count:byte)

Translation per item:
  - count:Int(N) -> Count:Byte(N)
  - components.minecraft:potion_contents.potion -> tag.Potion
  - components.minecraft:written_book_content.{title|author|pages|resolved} -> tag.{title|author|pages|resolved}
    - title.{raw|text} string -> tag.title (plain string)
    - author -> tag.author (plain string)
    - pages[i].{raw|text} -> tag.pages[i] = JSON-stringified component (json.dumps({"text": page_text}))
    - resolved -> tag.resolved (Byte)
  - bare items (no components) -> just count:Int -> Count:Byte rewrite
  - any unexpected component -> RAISE (don't silently strip)
"""
import json
import os
import shutil
import sys

import nbtlib
from nbtlib.tag import Compound, List, Int, Byte, String, Long, IntArray

REPO = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2-1.20-datapack"
STRUCT = os.path.join(REPO, "src", "main", "resources", "data", "mns", "structures")

PIECES = [
    # (rel path under structures/, structure-id-without-mns-prefix)
    "large_arena/l3.nbt",
    "large_arena/r3.nbt",
    "mega_fortress/start/mega_crossing_center_1.nbt",
    "mega_fortress/start/mega_crossing_east_straight_1.nbt",
    "mega_fortress/start/mega_crossing_north_straight_1.nbt",
]

# Known components we accept and know how to translate; any other component -> raise
KNOWN_COMPONENTS = {
    "minecraft:potion_contents",
    "minecraft:written_book_content",
}


def get_count(item: Compound) -> int:
    if "count" in item:
        return int(item["count"])
    if "Count" in item:
        return int(item["Count"])
    return 1


def translate_item(item: Compound) -> Compound:
    """Return a NEW Compound that is the legacy-tag form of `item`."""
    iid = str(item.get("id", ""))
    new = Compound()
    new["id"] = String(iid)
    new["Count"] = Byte(get_count(item))
    if "Slot" in item:
        # Slot is already Byte in containers - preserve as-is
        new["Slot"] = item["Slot"]
    elif "slot" in item:
        new["Slot"] = Byte(int(item["slot"]))

    components = item.get("components")
    if not isinstance(components, Compound) or len(components) == 0:
        # Bare item - no tag needed
        return new

    tag = Compound()

    for key, val in components.items():
        if key == "minecraft:potion_contents":
            # {potion: "minecraft:..."} -> tag.Potion = "minecraft:..."
            if not isinstance(val, Compound) or "potion" not in val:
                raise ValueError(f"Unexpected potion_contents shape on {iid}: {dict(val) if isinstance(val, Compound) else val!r}")
            potion = str(val["potion"])
            tag["Potion"] = String(potion)
            # Custom effects / custom color would also live here in extended cases - reject
            extras = [k for k in val.keys() if k != "potion"]
            if extras:
                raise ValueError(f"Unsupported potion_contents subfields on {iid}: {extras}")
        elif key == "minecraft:written_book_content":
            if not isinstance(val, Compound):
                raise ValueError(f"Unexpected written_book_content type on {iid}")
            wbc = val
            # title
            title = wbc.get("title")
            if isinstance(title, Compound):
                t_val = title.get("raw") if "raw" in title else title.get("text")
                if t_val is None:
                    raise ValueError(f"Empty Filterable title on {iid}")
                tag["title"] = String(str(t_val))
                extras = [k for k in title.keys() if k not in ("raw", "text", "filtered")]
                if extras:
                    raise ValueError(f"Unexpected title Filterable subfields: {extras}")
            elif title is not None:
                tag["title"] = String(str(title))
            # author
            if "author" in wbc:
                tag["author"] = String(str(wbc["author"]))
            # pages
            pages = wbc.get("pages")
            if isinstance(pages, List):
                legacy_pages = List[String]()
                for i, page in enumerate(pages):
                    if isinstance(page, Compound):
                        p_val = page.get("raw") if "raw" in page else page.get("text")
                        if p_val is None:
                            raise ValueError(f"Empty Filterable page {i} on {iid}")
                        page_text = str(p_val)
                        extras = [k for k in page.keys() if k not in ("raw", "text", "filtered")]
                        if extras:
                            raise ValueError(f"Unexpected page Filterable subfields: {extras}")
                    elif isinstance(page, String):
                        page_text = str(page)
                    else:
                        raise ValueError(f"Unexpected page type {type(page).__name__} on {iid}")
                    legacy_pages.append(String(json.dumps({"text": page_text})))
                tag["pages"] = legacy_pages
            # resolved
            if "resolved" in wbc:
                rv = wbc["resolved"]
                tag["resolved"] = Byte(1 if int(rv) else 0)
            # generation (optional, defaults 0)
            if "generation" in wbc:
                tag["generation"] = Int(int(wbc["generation"]))
        else:
            raise ValueError(f"Unknown component on {iid}: {key} (translator does not know how to legacy-ify this)")

    if len(tag) > 0:
        new["tag"] = tag
    return new


def downgrade_root(root: Compound) -> None:
    """In-place: translate every container/frame ItemStack in this structure NBT,
    and lower DataVersion to 3465 (MC 1.20.1)."""
    # Block entities
    for b in root.get("blocks", []):
        if not isinstance(b, Compound):
            continue
        be = b.get("nbt")
        if not isinstance(be, Compound):
            continue
        bid = str(be.get("id", ""))
        # Items[] containers
        items = be.get("Items")
        if isinstance(items, List) and len(items) > 0:
            new_items = List[Compound]()
            for it in items:
                if isinstance(it, Compound):
                    new_items.append(translate_item(it))
            be["Items"] = new_items
        # Lectern Book
        if "lectern" in bid:
            book = be.get("Book")
            if isinstance(book, Compound) and "id" in book:
                be["Book"] = translate_item(book)
            # Lecterns also use Page (int); leave as-is. Set Page=0 to open on page 1.
            if "Page" in be:
                be["Page"] = Int(0)
    # Item-frame entities
    for ew in root.get("entities", []):
        if not isinstance(ew, Compound):
            continue
        ent = ew.get("nbt")
        if not isinstance(ent, Compound):
            continue
        eid = str(ent.get("id", ""))
        if eid in ("minecraft:item_frame", "minecraft:glow_item_frame"):
            item = ent.get("Item")
            if isinstance(item, Compound) and "id" in item:
                ent["Item"] = translate_item(item)
    # DataVersion
    root["DataVersion"] = Int(3465)


def set_lectern_page_zero(root: Compound) -> int:
    """Set lectern BE Page=0 in-place. Used for the v1_20_5 variant where we don't downgrade items."""
    n = 0
    for b in root.get("blocks", []):
        if not isinstance(b, Compound):
            continue
        be = b.get("nbt")
        if not isinstance(be, Compound):
            continue
        if str(be.get("id", "")) == "minecraft:lectern":
            be["Page"] = Int(0)
            n += 1
    return n


def root_of(nbt):
    return nbt.root if hasattr(nbt, "root") else nbt


def process(rel: str):
    top = os.path.join(STRUCT, rel)
    v1_20_5 = os.path.join(STRUCT, "v1_20_5", rel)
    print(f"\n=== {rel} ===")
    if not os.path.exists(top):
        print(f"  ! MISSING top-level NBT, skipping")
        return False

    # 1) Copy current top-level to v1_20_5/<rel> (unchanged shape)
    os.makedirs(os.path.dirname(v1_20_5), exist_ok=True)
    shutil.copyfile(top, v1_20_5)
    # 1a) For lectern piece, also set Page=0 in v1_20_5 copy
    nbt = nbtlib.load(v1_20_5)
    r = root_of(nbt)
    n_pg = set_lectern_page_zero(r)
    if n_pg:
        nbt.save(v1_20_5, gzipped=True, byteorder='big')
        print(f"  v1_20_5: copy made; Page=0 set on {n_pg} lectern(s)")
    else:
        print(f"  v1_20_5: copy made (no lecterns)")

    # 2) Downgrade top-level: translate items, set Page=0, lower DataVersion to 3465
    nbt = nbtlib.load(top)
    r = root_of(nbt)
    old_dv = int(r.get("DataVersion", 0))
    try:
        downgrade_root(r)
        n_pg2 = set_lectern_page_zero(r)  # idempotent; downgrade_root already does for lecterns
    except Exception as e:
        print(f"  !! Translation FAILED on {rel}: {e}")
        # Revert v1_20_5 copy? No - it's a clean copy, harmless
        raise
    nbt.save(top, gzipped=True, byteorder='big')
    print(f"  top-level: legacy-tag form written (DataVersion {old_dv} -> 3465)")
    return True


def verify():
    print("\n=== Verification ===")
    for rel in PIECES:
        top = os.path.join(STRUCT, rel)
        v5 = os.path.join(STRUCT, "v1_20_5", rel)
        for label, path, expect_dv, expect_shape in [
            ("top-level (1.20.0-1.20.4)", top, 3465, "tag"),
            ("v1_20_5    (1.20.5-1.20.6)", v5, 4556, "components"),
        ]:
            nbt = nbtlib.load(path)
            r = root_of(nbt)
            dv = int(r.get("DataVersion", 0))
            # Inspect first item we find
            found_shape = "?"
            n_items = 0
            for b in r.get("blocks", []):
                if isinstance(b, Compound):
                    be = b.get("nbt")
                    if isinstance(be, Compound):
                        for it in be.get("Items", []) or []:
                            if isinstance(it, Compound) and "id" in it:
                                n_items += 1
                                if found_shape == "?":
                                    if "tag" in it:
                                        found_shape = "tag"
                                    elif "components" in it:
                                        found_shape = "components"
                                    else:
                                        found_shape = "bare"
                        book = be.get("Book")
                        if isinstance(book, Compound) and "id" in book:
                            n_items += 1
                            if found_shape == "?":
                                found_shape = "tag" if "tag" in book else ("components" if "components" in book else "bare")
            # Bare items don't carry the tag/components marker; check count_key
            count_key = "?"
            for b in r.get("blocks", []):
                if isinstance(b, Compound):
                    be = b.get("nbt")
                    if isinstance(be, Compound):
                        for it in be.get("Items", []) or []:
                            if isinstance(it, Compound):
                                if "Count" in it: count_key = "Count(byte)"
                                elif "count" in it: count_key = "count(int)"
                                break
                if count_key != "?": break
            ok_dv = dv == expect_dv
            shape_match = (found_shape in (expect_shape, "bare")) or (expect_shape == "components" and found_shape == "components") or (expect_shape == "tag" and found_shape == "tag")
            ok_count = (count_key == ("Count(byte)" if expect_shape == "tag" else "count(int)"))
            ok = ok_dv and shape_match and ok_count
            tag = "OK" if ok else "FAIL"
            print(f"  [{tag}] {rel:55s} {label}: DV={dv}/{expect_dv}, items={n_items}, schema={found_shape}, count_key={count_key}")


if __name__ == "__main__":
    ok_all = True
    for rel in PIECES:
        try:
            ok = process(rel)
            ok_all = ok_all and ok
        except Exception as e:
            ok_all = False
            print(f"  STOPPED on {rel}: {e}")
            break
    verify()
    sys.exit(0 if ok_all else 1)
