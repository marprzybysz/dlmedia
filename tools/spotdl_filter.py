#!/usr/bin/env python3
"""Filter a spotdl save-file (.spotdl = JSON array of song objects) to a subset.

Lets the user pick/range Spotify tracks: we reuse the metadata already fetched by
`spotdl save` and write a smaller .spotdl that `spotdl download` reads back — no
re-querying. Shared by the bash TUI and the (future) GUI so the selection logic
lives in one place. Qt-free and import-safe, so it's unit-tested.

Usage: spotdl_filter.py <in.spotdl> <spec> <out.spotdl>
  spec: 1-based comma/range list, e.g. "1,3,5" or "2-4,7". Out-of-range dropped.
Prints the number of tracks written; exits non-zero on malformed input.
"""
from __future__ import annotations

import json
import sys


def parse_spec(spec: str, n: int) -> list[int]:
    """Expand a "1,3,5" / "2-4,7" spec into sorted, de-duped 1-based indices in [1, n]."""
    idx: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            idx.update(range(int(a), int(b) + 1))
        else:
            idx.add(int(part))
    return [i for i in sorted(idx) if 1 <= i <= n]


def filter_file(in_path: str, spec: str, out_path: str) -> int:
    """Write the selected songs from `in_path` to `out_path`; return how many."""
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    picked = [data[i - 1] for i in parse_spec(spec, len(data))]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(picked, f, ensure_ascii=False)
    return len(picked)


if __name__ == "__main__":
    print(filter_file(sys.argv[1], sys.argv[2], sys.argv[3]))
