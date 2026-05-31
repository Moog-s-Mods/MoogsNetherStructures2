"""Full book inventory on 1.20-datapack — item frames, lecterns, containers.
Reports per-NBT: location of the book + current shape (components.* vs tag.*)."""
import os
import nbtlib
from nbtlib.tag import Compound, List

ROOT = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2-1.20-datapack\src\main\resources\data\mns"
BOOK_IDS = {"minecraft:written_book", "minecraft:writable_book"}


def inspect_item(item):
    """Return (shape, snippet) for an ItemStack-tagged Compound."""
    has_components = "components" in item and any(
        k in item["components"] for k in ("minecraft:written_book_content", "minecraft:writable_book_content")
    )
    has_tag = "tag" in item and any(
        k in item["tag"] for k in ("pages", "title", "author")
    )
    parts = []
    title = ""
    pages = 0
    if has_components:
        parts.append("components.*")
        wbc = item["components"].get("minecraft:written_book_content")
        if wbc is not None:
            t = wbc.get("title")
            if isinstance(t, Compound):
                title = str(t.get("raw", t.get("text", "")))
            elif t is not None:
                title = str(t)
            try:
                pages = len(wbc.get("pages", []))
            except Exception:
                pages = 0
    if has_tag:
        parts.append("tag.*")
        try:
            title = title or str(item["tag"].get("title", ""))
        except Exception:
            pass
        try:
            pages = max(pages, len(item["tag"].get("pages", [])))
        except Exception:
            pass
    if not parts:
        parts.append("EMPTY")
    return "+".join(parts), title[:60], pages


def main():
    hits = []
    for dp, _, fs in os.walk(ROOT):
        for n in fs:
            if not n.endswith(".nbt"):
                continue
            p = os.path.join(dp, n)
            try:
                nbt = nbtlib.load(p)
            except Exception as e:
                print(f"!! load error {p}: {e}")
                continue
            r = nbt.root if hasattr(nbt, "root") else nbt
            dv = r.get("DataVersion")
            # Entities (item_frame / glow_item_frame)
            for ew in r.get("entities", []):
                ent = ew.get("nbt") if isinstance(ew, Compound) else None
                if ent is None:
                    continue
                eid = str(ent.get("id", ""))
                if "item_frame" not in eid:
                    continue
                item = ent.get("Item")
                if item is None:
                    continue
                if str(item.get("id", "")) not in BOOK_IDS:
                    continue
                shape, title, pages = inspect_item(item)
                hits.append((p, dv, f"entity:{eid}", str(item.get("id")), shape, pages, title))
            # Block entities: lecterns (Book), containers (Items)
            for b in r.get("blocks", []):
                be = b.get("nbt") if isinstance(b, Compound) else None
                if be is None:
                    continue
                bid = str(be.get("id", ""))
                if "lectern" in bid:
                    book = be.get("Book")
                    if book is not None and str(book.get("id", "")) in BOOK_IDS:
                        shape, title, pages = inspect_item(book)
                        hits.append((p, dv, f"lectern:{bid}", str(book.get("id")), shape, pages, title))
                if "Items" in be:
                    for it in be.get("Items", []):
                        if str(it.get("id", "")) in BOOK_IDS:
                            shape, title, pages = inspect_item(it)
                            hits.append((p, dv, f"container:{bid}", str(it.get("id")), shape, pages, title))
    print(f"\nFound {len(hits)} book(s) on 1.20-datapack:")
    for h in hits:
        path, dv, loc, iid, shape, pages, title = h
        rel = path.split("data\\mns\\", 1)[-1]
        print(f"  {rel}")
        print(f"    DataVersion={dv}  via {loc}  item={iid}  shape={shape}  pages={pages}  title={title!r}")


if __name__ == "__main__":
    main()
