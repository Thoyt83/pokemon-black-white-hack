#!/usr/bin/env python3
"""Validate local Pokémon Black/White source ROMs without modifying them."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(os.environ.get("BW_ROM_SOURCE_DIR", ROOT / "roms" / "source")).resolve()

TARGETS = {
    "black": {
        "game_code": "IRBO",
        "title_prefix": "POKEMON B",
        "known_sha1": {
            "26ad0b9967aa279c4a266ee69f52b9b2332399a5",
        },
    },
    "white": {
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


def read_identity(path: Path) -> tuple[str, str] | None:
    with path.open("rb") as stream:
        header = stream.read(16)

    if len(header) != 16:
        return None

    title = header[:12].rstrip(b"\0").decode("ascii", errors="replace")
    game_code = header[12:16].decode("ascii", errors="replace")
    return title, game_code


def inspect_rom(label: str, path: Path, target: dict[str, object]) -> bool:
    identity = read_identity(path)
    if identity is None:
        print(f"[invalid] {label}: file is too small to contain an NDS header")
        return False

    title, game_code = identity
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
    print(f"  file:      {path.name}")
    print(f"  title:     {title}")
    print(f"  game code: {game_code} (expected {expected_code})")
    print(f"  size:      {size:,} bytes")
    print(f"  sha1:      {digest}")
    print(f"  baseline:  {'recognized clean full dump' if hash_known else 'unknown; review before building'}")

    return header_ok


def main() -> int:
    candidates = sorted(SOURCE_DIR.glob("*.nds")) if SOURCE_DIR.is_dir() else []
    matches: dict[str, list[Path]] = {label: [] for label in TARGETS}

    for path in candidates:
        identity = read_identity(path)
        if identity is None:
            continue
        _, game_code = identity
        for label, target in TARGETS.items():
            if game_code == target["game_code"]:
                matches[label].append(path)

    results: list[bool] = []
    for label, target in TARGETS.items():
        paths = matches[label]
        if not paths:
            print(f"[missing] {label}: no {target['game_code']} ROM found in {SOURCE_DIR}")
            results.append(False)
        elif len(paths) > 1:
            names = ", ".join(path.name for path in paths)
            print(f"[ambiguous] {label}: multiple matching ROMs found: {names}")
            results.append(False)
        else:
            results.append(inspect_rom(label, paths[0], target))

    if all(results):
        print("\nBoth game headers are valid. Review any unknown hashes before selecting the build baseline.")
        return 0

    print(f"\nAdd one clean English Black and White dump to {SOURCE_DIR}.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

