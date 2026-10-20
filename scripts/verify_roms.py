#!/usr/bin/env python3
"""Validate local Pokémon Black/White source ROMs without modifying them."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

TARGETS = {
    "black": {
        "path": ROOT / "roms" / "source" / "pokemon_black.nds",
        "game_code": "IRBO",
        "title_prefix": "POKEMON B",
        "known_sha1": {
            "26ad0b9967aa279c4a266ee69f52b9b2332399a5",
        },
    },
    "white": {
        "path": ROOT / "roms" / "source" / "pokemon_white.nds",
        "game_code": "IRAO",
        "title_prefix": "POKEMON W",
        "known_sha1": {
            "bc696a0dfb448c7b3a8a206f0f8214411a039208",
        },
    },
}


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_rom(label: str, target: dict[str, object]) -> bool:
    path = target["path"]
    assert isinstance(path, Path)

    if not path.is_file():
        print(f"[missing] {label}: {path.relative_to(ROOT)}")
        return False

    with path.open("rb") as stream:
        header = stream.read(16)

    if len(header) != 16:
        print(f"[invalid] {label}: file is too small to contain an NDS header")
        return False

    title = header[:12].rstrip(b"\0").decode("ascii", errors="replace")
    game_code = header[12:16].decode("ascii", errors="replace")
    digest = sha1_file(path)
    size = path.stat().st_size

    expected_code = target["game_code"]
    expected_title = target["title_prefix"]
    known_hashes = target["known_sha1"]
    assert isinstance(expected_code, str)
    assert isinstance(expected_title, str)
    assert isinstance(known_hashes, set)

    header_ok = game_code == expected_code and title.startswith(expected_title)
    hash_known = digest in known_hashes

    print(f"[{ 'ok' if header_ok else 'invalid' }] {label}")
    print(f"  title:     {title}")
    print(f"  game code: {game_code} (expected {expected_code})")
    print(f"  size:      {size:,} bytes")
    print(f"  sha1:      {digest}")
    print(f"  baseline:  {'recognized clean full dump' if hash_known else 'unknown; review before building'}")

    return header_ok


def main() -> int:
    results = [inspect_rom(label, target) for label, target in TARGETS.items()]
    if all(results):
        print("\nBoth game headers are valid. Review any unknown hashes before selecting the build baseline.")
        return 0

    print("\nAdd clean English Black and White dumps at the paths shown above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

