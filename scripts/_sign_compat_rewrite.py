"""Downgrade four MNS structure NBTs so their sign messages load on 1.21.0-1.21.4.

Root cause: signs exported from the 1.21.10 build world store each `messages`
entry as a bare NBT String (e.g. String('')). The 1.21.0-1.21.4 Component
codec requires each entry to be valid JSON. `json.loads('')` throws. Fix:
JSON-encode each bare value ('' → '""').

Also applies the same fix to `filtered_messages` if present (same shape).

The `messages` list contains plain String tags in these files (NOT {raw:…}
Compounds — that shape is for written_book_content pages). The fix handles
both shapes defensively.

Layout produced per piece:
  - top-level <path>   ← DataVersion 3953 + JSON-encoded messages (1.21.0-1.21.4)
  - v1_21_5/<path>     ← original file (1.21.5+ shape, bare-string messages)

Pieces that already have a top-level DV of 3953 (Piece 1) skip the DV edit
but still get the message encoding fix.

Idempotent: a message already starting AND ending with '"' is left alone.
"""
import json
import os
import shutil
import sys

import nbtlib
from nbtlib.tag import Compound, Int, List, String

REPO = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2"
STRUCT = os.path.join(REPO, "src", "main", "resources", "data", "mns", "structure")

DATAVERSION_1_21_0 = 3953

# (relative path under structure/, needs_dv_lower, needs_v1_21_5_mirror)
PIECES = [
    # Piece 1 — already DV 3953, v1_21_5/ mirror already exists from book fix
    ("mega_fortress/start/mega_crossing_north_straight_1.nbt", False, False),
    # Piece 2 — DV 4556, no v1_21_5/ mirror yet
    ("mega_fortress/crossings/small/lower/small_crossing_east_lower_1.nbt", True, True),
    # Piece 3 — DV 4556, no v1_21_5/ mirror yet
    ("houses/large_house_1.nbt", True, True),
    # Piece 4 — DV 4556, no mirror at all yet
    ("crimson_forge.nbt", True, True),
]


def load(path):
    return nbtlib.load(path)


def save(nbt, path):
    nbt.save(path, gzipped=True, byteorder="big")


def root_of(nbt):
    return nbt.root if hasattr(nbt, "root") else nbt


def fix_sign_messages(node, counter):
    """Walk the NBT tree and JSON-encode any bare sign message strings."""
    if isinstance(node, Compound):
        be_id = str(node.get("id", ""))
        if be_id in ("minecraft:sign", "minecraft:hanging_sign"):
            for side in ("front_text", "back_text"):
                text = node.get(side)
                if not isinstance(text, Compound):
                    continue
                for field in ("messages", "filtered_messages"):
                    msgs = text.get(field)
                    if not isinstance(msgs, List):
                        continue
                    for i, m in enumerate(msgs):
                        if isinstance(m, Compound) and "raw" in m:
                            # Filterable<Component> shape
                            cur = str(m["raw"])
                            if not (cur.startswith('"') and cur.endswith('"')):
                                m["raw"] = String(json.dumps(cur))
                                counter[0] += 1
                        elif isinstance(m, String):
                            # Plain String shape (what these files actually use)
                            cur = str(m)
                            try:
                                json.loads(cur)  # already valid JSON — skip
                            except (json.JSONDecodeError, ValueError):
                                msgs[i] = String(json.dumps(cur))
                                counter[0] += 1
        for v in node.values():
            fix_sign_messages(v, counter)
    elif isinstance(node, List):
        for it in node:
            fix_sign_messages(it, counter)


def v1_21_5_path(rel):
    """Return the mirror path for v1_21_5.

    mega_fortress pieces live at:  structure/mega_fortress/v1_21_5/<rest>
    All other pieces live at:      structure/v1_21_5/<rel>
    """
    if rel.startswith("mega_fortress/"):
        rest = rel[len("mega_fortress/"):]
        return os.path.join(STRUCT, "mega_fortress", "v1_21_5", rest)
    return os.path.join(STRUCT, "v1_21_5", rel)


def process_piece(rel, needs_dv_lower, needs_v1_21_5_mirror):
    top = os.path.join(STRUCT, rel)

    print(f"\n=== {rel} ===")

    if not os.path.exists(top):
        print(f"  ! MISSING top-level NBT, aborting this piece")
        return False

    # 1) Mirror current top-level (1.21.5+ shape) to v1_21_5/<rel>
    if needs_v1_21_5_mirror:
        v5 = v1_21_5_path(rel)
        os.makedirs(os.path.dirname(v5), exist_ok=True)
        shutil.copyfile(top, v5)
        print(f"  copied top-level -> v1_21_5/")
    else:
        print(f"  skipping v1_21_5 mirror (already exists or not needed)")

    # 2) Downgrade top-level: lower DataVersion if needed, JSON-encode messages
    nbt = load(top)
    r = root_of(nbt)
    old_dv = int(r.get("DataVersion", 0))

    if needs_dv_lower:
        r["DataVersion"] = Int(DATAVERSION_1_21_0)

    counter = [0]
    fix_sign_messages(r, counter)

    save(nbt, top)
    dv_note = f"DataVersion {old_dv} -> {DATAVERSION_1_21_0}, " if needs_dv_lower else f"DataVersion unchanged ({old_dv}), "
    print(f"  top-level: {dv_note}JSON-encoded {counter[0]} message(s)")
    return True


def verify():
    print("\n=== Verification ===")
    for rel, needs_dv_lower, needs_v1_21_5_mirror in PIECES:
        # Check top-level
        top = os.path.join(STRUCT, rel)
        if not os.path.exists(top):
            print(f"  ! MISSING: {top}")
        else:
            nbt = load(top)
            r = root_of(nbt)
            dv = int(r.get("DataVersion", 0))
            sample = _sample_first_message(r)
            encoded = (sample.startswith('"') and sample.endswith('"')) if sample is not None else None
            ok_dv = (dv == DATAVERSION_1_21_0)
            status = "OK" if (ok_dv and encoded) else "FAIL"
            print(
                f"  [{status}] top-level {rel}: DV={dv}"
                + (f" (want {DATAVERSION_1_21_0})" if not ok_dv else "")
                + (f", msg0={'json-encoded' if encoded else 'bare-string'}" if sample is not None else ", no messages found")
            )

        # Check v1_21_5 mirror
        if needs_v1_21_5_mirror:
            v5 = v1_21_5_path(rel)
            if not os.path.exists(v5):
                print(f"  ! MISSING v1_21_5: {v5}")
            else:
                nbt = load(v5)
                r = root_of(nbt)
                dv = int(r.get("DataVersion", 0))
                sample = _sample_first_message(r)
                encoded = (sample.startswith('"') and sample.endswith('"')) if sample is not None else None
                bare = not encoded if encoded is not None else None
                status = "OK" if (dv != DATAVERSION_1_21_0 and bare) else ("WARN-already-encoded" if encoded else "OK")
                print(
                    f"  [{status}] v1_21_5/ {rel}: DV={dv}"
                    + (f", msg0={'bare-string' if bare else 'json-encoded'}" if sample is not None else ", no messages found")
                )


def _sample_first_message(node):
    """Return the first sign message string found in the tree, or None."""
    if isinstance(node, Compound):
        be_id = str(node.get("id", ""))
        if be_id in ("minecraft:sign", "minecraft:hanging_sign"):
            for side in ("front_text", "back_text"):
                text = node.get(side)
                if not isinstance(text, Compound):
                    continue
                msgs = text.get("messages")
                if isinstance(msgs, List) and msgs:
                    m = msgs[0]
                    if isinstance(m, String):
                        return str(m)
                    if isinstance(m, Compound) and "raw" in m:
                        return str(m["raw"])
        for v in node.values():
            x = _sample_first_message(v)
            if x is not None:
                return x
    elif isinstance(node, List):
        for it in node:
            x = _sample_first_message(it)
            if x is not None:
                return x
    return None


if __name__ == "__main__":
    all_ok = True
    for rel, needs_dv_lower, needs_v1_21_5_mirror in PIECES:
        ok = process_piece(rel, needs_dv_lower, needs_v1_21_5_mirror)
        all_ok = all_ok and ok
    verify()
    sys.exit(0 if all_ok else 1)
