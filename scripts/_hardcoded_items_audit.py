"""Audit hard-coded items in MNS 1.20-datapack structure NBTs.

Walks every .nbt under data/mns/, finds containers (block entities with Items[] or Book,
and item_frame entities with Item), and distinguishes hard-coded contents
(populated Items[] / Book / Item) from loot-table-driven (LootTable field present).

Reports per NBT: hard-coded slots only. Schema (tag.* / components.* / bare).
"""
import os
import sys
import nbtlib
from nbtlib.tag import Compound, List

ROOT = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2-1.20-datapack\src\main\resources\data\mns"

CONTAINER_BE_IDS = {
    "minecraft:chest", "minecraft:trapped_chest", "minecraft:barrel",
    "minecraft:dispenser", "minecraft:dropper", "minecraft:hopper",
    "minecraft:furnace", "minecraft:blast_furnace", "minecraft:smoker",
    "minecraft:brewing_stand", "minecraft:lectern",
    "minecraft:shulker_box",
    # color shulker variants below handled by suffix-match
}
FRAME_ENTITY_IDS = {"minecraft:item_frame", "minecraft:glow_item_frame"}


def is_container_be(bid: str) -> bool:
    if bid in CONTAINER_BE_IDS:
        return True
    if bid.endswith("_shulker_box"):
        return True
    return False


def item_schema(item: Compound) -> str:
    has_tag = "tag" in item and isinstance(item.get("tag"), Compound) and len(item["tag"]) > 0
    has_components = "components" in item and isinstance(item.get("components"), Compound) and len(item["components"]) > 0
    if has_tag and has_components:
        return "tag+components(!)"
    if has_tag:
        return "tag.*"
    if has_components:
        return "components.*"
    return "bare"


def count_of(item: Compound) -> str:
    if "count" in item:
        return f"{int(item['count'])}"
    if "Count" in item:
        return f"{int(item['Count'])}"
    return "?"


def book_title(item: Compound) -> str:
    """Pull a title snippet if this is a written/writable book."""
    iid = str(item.get("id", ""))
    if iid not in ("minecraft:written_book", "minecraft:writable_book"):
        return ""
    # components.minecraft:written_book_content.title.{raw|text}
    comps = item.get("components")
    if isinstance(comps, Compound):
        wbc = comps.get("minecraft:written_book_content")
        if isinstance(wbc, Compound):
            t = wbc.get("title")
            if isinstance(t, Compound):
                v = t.get("raw") if "raw" in t else t.get("text")
                if v is not None:
                    return f' "{str(v)[:40]}"'
            elif t is not None:
                return f' "{str(t)[:40]}"'
    # legacy tag.title
    tag = item.get("tag")
    if isinstance(tag, Compound) and "title" in tag:
        return f' "{str(tag["title"])[:40]}"'
    return ""


def pos_str(b):
    p = b.get("pos") if isinstance(b, Compound) else None
    if p is None:
        return "?"
    try:
        return f"({int(p[0])},{int(p[1])},{int(p[2])})"
    except Exception:
        return str(p)


def slot_of(it):
    if isinstance(it, Compound):
        if "Slot" in it:
            return int(it["Slot"])
        if "slot" in it:
            return int(it["slot"])
    return -1


def walk_nbt(path: str):
    """Yield (kind, container_id, position, items, loot_table_id, extras) for each container
    found in the NBT.
    kind = 'be-items' | 'be-book' | 'frame' | 'be-loot'
    """
    try:
        nbt = nbtlib.load(path)
    except Exception as e:
        return [("error", "load", "-", [], None, str(e))]
    root = nbt.root if hasattr(nbt, "root") else nbt
    dv = int(root.get("DataVersion", 0))
    out = []

    # Block entities
    for b in root.get("blocks", []):
        if not isinstance(b, Compound):
            continue
        be = b.get("nbt")
        if be is None:
            continue
        bid = str(be.get("id", ""))
        if not (is_container_be(bid) or "lectern" in bid):
            continue
        pos = pos_str(b)
        loot_id = str(be["LootTable"]) if "LootTable" in be else None

        # Items[] (chests, dispensers, droppers, hoppers, furnaces, barrels, brewing_stand, shulker)
        items_list = be.get("Items")
        items_populated = isinstance(items_list, List) and len(items_list) > 0
        if items_populated:
            slot_dump = []
            for it in items_list:
                if not isinstance(it, Compound):
                    continue
                slot = slot_of(it)
                iid = str(it.get("id", "?"))
                cnt = count_of(it)
                sch = item_schema(it)
                title = book_title(it)
                slot_dump.append((slot, iid, cnt, sch, title))
            out.append(("be-items", bid, pos, slot_dump, loot_id, dv))
        elif loot_id:
            out.append(("be-loot", bid, pos, [], loot_id, dv))

        # Lectern: 'Book' field (single ItemStack)
        if "lectern" in bid:
            book = be.get("Book")
            if isinstance(book, Compound) and "id" in book:
                slot_dump = [(0, str(book.get("id", "?")), count_of(book), item_schema(book), book_title(book))]
                out.append(("be-book", bid, pos, slot_dump, loot_id, dv))

    # Item frames (entities)
    for ew in root.get("entities", []):
        if not isinstance(ew, Compound):
            continue
        ent = ew.get("nbt")
        if not isinstance(ent, Compound):
            continue
        eid = str(ent.get("id", ""))
        if eid not in FRAME_ENTITY_IDS:
            continue
        item = ent.get("Item")
        if not isinstance(item, Compound) or "id" not in item:
            continue
        bp = ew.get("blockPos")
        try:
            pos = f"({int(bp[0])},{int(bp[1])},{int(bp[2])})" if bp is not None else "?"
        except Exception:
            pos = "?"
        slot_dump = [(0, str(item.get("id", "?")), count_of(item), item_schema(item), book_title(item))]
        out.append(("frame", eid, pos, slot_dump, None, dv))

    return out


def main():
    by_family = {}  # family -> list of (rel_path, results)
    err_files = []

    for dp, _, fs in os.walk(ROOT):
        for n in fs:
            if not n.endswith(".nbt"):
                continue
            p = os.path.join(dp, n)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            family = rel.split("/")[1] if rel.startswith("structures/") and "/" in rel[len("structures/"):] else rel.split("/")[0]
            # structures/<family>/... or top-level segment
            if rel.startswith("structures/"):
                parts = rel[len("structures/"):].split("/")
                family = parts[0] if len(parts) > 1 else "structures/_top"
            else:
                family = rel.split("/")[0]
            results = walk_nbt(p)
            # Only retain NBTs that have at least one hard-coded result OR a frame (frame is always hard-coded)
            hardcoded = [r for r in results if r[0] in ("be-items", "be-book", "frame")]
            loot_only = [r for r in results if r[0] == "be-loot"]
            errs = [r for r in results if r[0] == "error"]
            if errs:
                err_files.append((rel, errs))
            if hardcoded or loot_only:
                by_family.setdefault(family, []).append((rel, hardcoded, loot_only, results))

    # === Print: per-family hard-coded inventory, then loot-only summary ===
    total_hc = 0
    total_loot = 0
    fam_totals = []
    for fam in sorted(by_family):
        files = by_family[fam]
        hc_files = [f for f in files if f[1]]  # has hardcoded
        loot_files = [f for f in files if f[2] and not f[1]]
        n_hc_slots = sum(len(items) for f in hc_files for (_kind, _bid, _pos, items, _lt, _dv) in f[1])
        n_loot_containers = sum(len(f[2]) for f in files)
        fam_totals.append((fam, len(hc_files), n_hc_slots, len(loot_files), n_loot_containers))

    print("=" * 80)
    print("MNS 1.20-datapack — hard-coded container/item audit")
    print("=" * 80)
    print()
    print("FAMILY-LEVEL SUMMARY")
    print(f"{'family':30s}  {'#NBTs(hardcoded)':>17s}  {'#hc slots':>10s}  {'#NBTs(loot-only)':>17s}  {'#loot containers':>18s}")
    for fam, n_hc_files, n_slots, n_loot_files, n_loot_c in fam_totals:
        total_hc += n_hc_files
        total_loot += n_loot_c
        print(f"{fam:30s}  {n_hc_files:>17d}  {n_slots:>10d}  {n_loot_files:>17d}  {n_loot_c:>18d}")
    print()

    print("=" * 80)
    print("HARD-CODED DETAILS (per file)")
    print("=" * 80)

    # Per-family detail dump
    for fam in sorted(by_family):
        files = by_family[fam]
        hc_files = [f for f in files if f[1]]
        if not hc_files:
            continue
        print(f"\n--- family: {fam} ({len(hc_files)} hard-coded NBT(s)) ---")
        for rel, hardcoded, _loot_only, _all in hc_files:
            # DataVersion from first entry
            dv = hardcoded[0][5] if hardcoded else 0
            print(f"\n  {rel}   [DataVersion={dv}]")
            for kind, bid, pos, slots, lt, _dv in hardcoded:
                tag_loot = f"   (also has LootTable={lt})" if lt else ""
                if kind == "frame":
                    print(f"    item_frame entity at {pos}{tag_loot}")
                elif kind == "be-book":
                    print(f"    {bid} at {pos} — Book field populated{tag_loot}")
                else:
                    print(f"    {bid} at {pos} — Items[]{tag_loot}")
                for slot, iid, cnt, sch, title in slots:
                    schema_tag = sch if sch != "bare" else ""
                    schema_str = f" [{schema_tag}]" if schema_tag else ""
                    slot_str = f"Slot {slot}: " if slot >= 0 else ""
                    print(f"      {slot_str}{iid} x{cnt}{title}{schema_str}")

    print()
    print("=" * 80)
    print("LOOT-TABLE-ONLY CONTAINERS (summary — no hard-coded items)")
    print("=" * 80)
    # Aggregate loot-table refs across all NBTs
    loot_refs = {}
    for fam in sorted(by_family):
        for rel, _hc, loot_only, _all in by_family[fam]:
            for kind, bid, pos, _slots, lt, dv in loot_only:
                loot_refs[lt] = loot_refs.get(lt, 0) + 1
    if loot_refs:
        for lt, n in sorted(loot_refs.items(), key=lambda kv: -kv[1]):
            print(f"  {n:>4d}× {lt}")
    else:
        print("  (none)")

    if err_files:
        print()
        print("=" * 80)
        print(f"LOAD ERRORS ({len(err_files)})")
        print("=" * 80)
        for rel, errs in err_files:
            for _k, _w, _p, _i, _lt, msg in errs:
                print(f"  {rel}: {msg}")


if __name__ == "__main__":
    main()
