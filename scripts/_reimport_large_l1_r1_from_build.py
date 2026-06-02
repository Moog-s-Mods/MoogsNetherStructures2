"""One-shot: reimport large_arena/{l1,r1}.nbt from the 1.21.10 build world
into 1.20-datapack, translating DV + palette + BE state inline.

The canonical porter (`_port_arenas_from_1_21.py`) reads from the
1.21-datapack source tree; this script bypasses that and reads from the
build-world saves folder directly. Use when a piece has been re-saved in
the build world but the 1.21-datapack tree hasn't been updated yet.
"""
import os
import sys

# Reuse the porter's translation primitives.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nbtlib  # noqa: E402
from nbtlib.tag import Compound, Int  # noqa: E402

import _port_arenas_from_1_21 as porter  # noqa: E402

BUILD_WORLD_LARGE = (
    r"C:\Users\finn\curseforge\minecraft\Instances\1.21.10 fabric (1)"
    r"\structures\mns\large_arena"
)
DST_STRUCT = porter.DST_STRUCT
DV_LEGACY = porter.DV_LEGACY

PIECES = ["l1.nbt", "r1.nbt"]
ARENA = "large_arena"


def main():
    for fn in PIECES:
        src = os.path.join(BUILD_WORLD_LARGE, fn)
        dst = os.path.join(DST_STRUCT, ARENA, fn)
        if not os.path.exists(src):
            print(f"SKIP missing source: {src}", file=sys.stderr)
            continue
        root = nbtlib.load(src)
        root["DataVersion"] = Int(DV_LEGACY)
        vault_idx, trial_idx = porter.sub_palette(root, ARENA)
        porter.rewrite_block_entities(root, vault_idx, trial_idx, ARENA, legacy_items=True)
        porter.translate_entities(root, legacy_items=True)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        root.save(dst, gzipped=True)
        print(f"{fn}: vault->barrel x{len(vault_idx)}, "
              f"trial->spawner x{len(trial_idx)}, DV->{DV_LEGACY} -> {dst}")


if __name__ == "__main__":
    main()
