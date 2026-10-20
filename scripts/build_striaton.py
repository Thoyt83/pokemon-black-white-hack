#!/usr/bin/env python3
"""Build the first playable Black/White Vanilla+ Striaton test ROMs.

The script patches the existing trainer-party NARC in place. It deliberately
does not rebuild the Nintendo DS filesystem, so DSi-enhanced data, padding, and
all unrelated bytes remain exactly as they were in the clean source dump.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct

import ndspy.rom


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(os.environ.get("BW_ROM_SOURCE_DIR", ROOT / "roms" / "source")).resolve()
BUILD_DIR = ROOT / "build" / "striaton"
DESIGN_PATH = ROOT / "data" / "design" / "boss_teams.json"
REFERENCE_PATH = ROOT / "data" / "reference" / "gen5_ids.json"
TRPOKE_PATH = "a/0/9/3"

GAME_CODES = {
    "IRBO": "black",
    "IRAO": "white",
}

PARTY_MEMBER = struct.Struct("<BBHHH4H")


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_roms(source: Path, output: Path, allowed_start: int, allowed_end: int) -> tuple[int, int]:
    changed = 0
    changed_outside_target = 0
    offset = 0
    with source.open("rb") as source_stream, output.open("rb") as output_stream:
        while True:
            source_chunk = source_stream.read(1024 * 1024)
            output_chunk = output_stream.read(1024 * 1024)
            if not source_chunk and not output_chunk:
                break
            if len(source_chunk) != len(output_chunk):
                raise RuntimeError("Source and output lengths differ during verification")
            for index, (before, after) in enumerate(zip(source_chunk, output_chunk)):
                if before == after:
                    continue
                absolute_offset = offset + index
                changed += 1
                if not allowed_start <= absolute_offset < allowed_end:
                    changed_outside_target += 1
            offset += len(source_chunk)
    return changed, changed_outside_target


def read_game_code(path: Path) -> str:
    with path.open("rb") as stream:
        stream.seek(12)
        return stream.read(4).decode("ascii", errors="replace")


def discover_sources() -> dict[str, Path]:
    sources: dict[str, Path] = {}
    for path in sorted(SOURCE_DIR.glob("*.nds")):
        label = GAME_CODES.get(read_game_code(path))
        if label is None:
            continue
        if label in sources:
            raise RuntimeError(f"Multiple {label} ROMs found in {SOURCE_DIR}")
        sources[label] = path

    missing = sorted(set(GAME_CODES.values()) - set(sources))
    if missing:
        raise RuntimeError(f"Missing source ROMs: {', '.join(missing)}")
    return sources


def load_striaton_design() -> tuple[list[dict[str, object]], dict[str, dict[str, int]]]:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    references = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    battles = [
        battle
        for battle in design["battles"]
        if battle["key"].startswith("striaton_")
    ]
    if len(battles) != 3:
        raise RuntimeError("Expected exactly three Striaton battle definitions")
    return battles, references


def encode_lead(
    pokemon: dict[str, object], references: dict[str, dict[str, int]]
) -> bytes:
    species_name = pokemon["species"]
    move_names = pokemon["moves"]
    assert isinstance(species_name, str)
    assert isinstance(move_names, list)

    species_id = references["species"][species_name]
    move_ids = [references["moves"][name] for name in move_names]
    if len(move_ids) > 4:
        raise RuntimeError(f"Too many moves for {species_name}")
    move_ids.extend([0] * (4 - len(move_ids)))

    return PARTY_MEMBER.pack(
        50,  # Preserve the vanilla lead's difficulty/IV value.
        0,   # Default ability/gender selector.
        int(pokemon["level"]),
        species_id,
        0,   # Base form.
        *move_ids,
    )


def file_bounds(source: Path, rom: ndspy.rom.NintendoDSRom, internal_path: str) -> tuple[int, int]:
    file_id = rom.filenames.idOf(internal_path)
    if file_id is None:
        raise RuntimeError(f"ROM does not contain {internal_path}")

    with source.open("rb") as stream:
        stream.seek(0x48)
        fat_offset, fat_size = struct.unpack("<II", stream.read(8))
        if file_id * 8 + 8 > fat_size:
            raise RuntimeError(f"File ID {file_id} lies outside the ROM FAT")
        stream.seek(fat_offset + file_id * 8)
        return struct.unpack("<II", stream.read(8))


def narc_file_bounds(data: bytes, file_id: int) -> tuple[int, int]:
    if data[0x10:0x14] != b"BTAF":
        raise RuntimeError("Trainer archive does not contain the expected BTAF block")
    fat_block_size = struct.unpack_from("<I", data, 0x14)[0]
    file_count = struct.unpack_from("<H", data, 0x18)[0]
    if not 0 <= file_id < file_count:
        raise RuntimeError(f"NARC file ID {file_id} is out of range")

    relative_start, relative_end = struct.unpack_from(
        "<II", data, 0x1C + file_id * 8
    )
    image_block = data.find(b"GMIF", 0x10 + fat_block_size)
    if image_block < 0:
        raise RuntimeError("Trainer archive does not contain the expected GMIF block")
    data_start = image_block + 8
    return data_start + relative_start, data_start + relative_end


def patch_game(
    label: str,
    source: Path,
    battles: list[dict[str, object]],
    references: dict[str, dict[str, int]],
) -> dict[str, object]:
    rom = ndspy.rom.NintendoDSRom.fromFile(source)
    original_narc = rom.getFileByName(TRPOKE_PATH)
    patched_narc = bytearray(original_narc)
    changes: list[dict[str, object]] = []

    for battle in battles:
        trainer_id = int(battle["trainer_id"])
        party = battle["party"]
        assert isinstance(party, list) and len(party) == 2

        party_start, party_end = narc_file_bounds(original_narc, trainer_id)
        original_party = original_narc[party_start:party_end]
        if len(original_party) != PARTY_MEMBER.size * 2:
            raise RuntimeError(
                f"Trainer {trainer_id} has unexpected party size {len(original_party)}"
            )

        ace = PARTY_MEMBER.unpack(original_party[PARTY_MEMBER.size:])
        ace_species = references["species"][party[1]["species"]]
        if ace[2] != int(party[1]["level"]) or ace[3] != ace_species:
            raise RuntimeError(
                f"Trainer {trainer_id}'s vanilla ace does not match the design baseline"
            )

        new_lead = encode_lead(party[0], references)
        patched_narc[party_start:party_start + PARTY_MEMBER.size] = new_lead
        changes.append(
            {
                "key": battle["key"],
                "trainer_id": trainer_id,
                "lead_species": party[0]["species"],
                "lead_level": party[0]["level"],
                "lead_moves": party[0]["moves"],
                "ace_preserved": party[1]["species"],
            }
        )

    start, end = file_bounds(source, rom, TRPOKE_PATH)
    if end - start != len(original_narc):
        raise RuntimeError("FAT bounds do not match the trainer NARC length")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output = BUILD_DIR / f"pokemon_{label}_vanilla_plus_striaton.nds"
    shutil.copyfile(source, output)
    with output.open("r+b") as stream:
        stream.seek(start)
        stream.write(patched_narc)

    if output.stat().st_size != source.stat().st_size:
        raise RuntimeError("Output ROM size changed unexpectedly")

    changed_bytes = sum(a != b for a, b in zip(original_narc, patched_narc))
    rom_changed_bytes, unrelated_changed_bytes = compare_roms(source, output, start, end)
    if rom_changed_bytes != changed_bytes or unrelated_changed_bytes:
        raise RuntimeError(
            "Output verification found changes outside the intended trainer records"
        )
    return {
        "game": label,
        "game_code": read_game_code(source),
        "source_file": source.name,
        "source_sha1": sha1_file(source),
        "output_file": output.name,
        "output_sha1": sha1_file(output),
        "output_size": output.stat().st_size,
        "patched_internal_file": TRPOKE_PATH,
        "patched_offset": start,
        "patched_length": len(patched_narc),
        "changed_bytes_in_narc": changed_bytes,
        "changed_bytes_in_rom": rom_changed_bytes,
        "unrelated_bytes_changed": unrelated_changed_bytes,
        "changes": changes,
    }


def main() -> int:
    sources = discover_sources()
    battles, references = load_striaton_design()
    builds = [
        patch_game(label, source, battles, references)
        for label, source in sorted(sources.items())
    ]

    manifest = {
        "milestone": "striaton",
        "patch_method": "in-place NARC replacement",
        "builds": builds,
    }
    manifest_path = BUILD_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for build in builds:
        print(
            f"Built {build['game']}: {build['output_file']} "
            f"({build['changed_bytes_in_narc']} trainer-NARC bytes changed)"
        )
        print(f"  sha1: {build['output_sha1']}")
    print(f"Manifest: {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
