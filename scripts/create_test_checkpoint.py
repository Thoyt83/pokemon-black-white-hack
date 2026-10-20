#!/usr/bin/env python3
"""Create a disposable Gen 5 save positioned at the Striaton Gym.

This is a save-data checkpoint, not a copyrighted ROM/save artifact. It copies
the supplied local save, changes only the player position, first-gym completion
flags, and Trio Badge bit, then recalculates the affected BW block CRC16s in the
primary and backup save areas (both in-block and mirrored checksum fields).
The source save is never modified.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

import ndspy.narc
import ndspy.rom


SAVE_SIZE = 0x80000
BACKUP_BASE = 0x24000
POSITION_BLOCK = (0x19500, 0x009C, 0x1959E, 0x23F38)
EVENT_WORK_BLOCK = (0x20100, 0x03EC, 0x204EE, 0x23F5A)
MISC_BLOCK = (0x21200, 0x00EC, 0x212EE, 0x23F68)
CHECKSUM_BLOCK = (0x23F00, 0x008C, 0x23F9A, 0x23F9A)
EVENT_FLAGS_BASE = 0x2037C
POSITION_OFFSETS = {"map_id": 0x80, "x": 0x86, "z": 0x8A, "y": 0x8E}
MISC_BADGES_OFFSET = 0x04
TRIO_BADGE_MASK = 0x01


def crc16_ccitt(data: bytes | bytearray) -> int:
    """CRC-16/CCITT with init=0xFFFF and poly=0x1021 (BW save block CRC)."""
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def set_flag(save: bytearray, save_base: int, flag_id: int, enabled: bool) -> None:
    offset = save_base + EVENT_FLAGS_BASE + flag_id // 8
    mask = 1 << (flag_id % 8)
    if enabled:
        save[offset] |= mask
    else:
        save[offset] &= ~mask


def checkpoint_position(rom_path: Path, map_id: int) -> tuple[int, int, int, int]:
    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))
    zones = ndspy.narc.NARC(rom.getFileByName("a/0/1/2")).files[0]
    entry_size = 0x30
    if len(zones) % entry_size:
        raise ValueError("BW zonedata archive has an unexpected record size")
    start = map_id * entry_size
    if start + entry_size > len(zones):
        raise ValueError(f"Map ID {map_id} is outside the zonedata table")
    entry = zones[start : start + entry_size]
    encoded_map_id = struct.unpack_from("<H", entry, 0x16)[0]
    if encoded_map_id != map_id:
        raise ValueError(f"Zonedata record {map_id} encodes map ID {encoded_map_id}")
    x = struct.unpack_from("<H", entry, 0x24)[0]
    z = struct.unpack_from("<H", entry, 0x28)[0]
    y = struct.unpack_from("<H", entry, 0x2C)[0]
    return encoded_map_id, x, z, y


def update_block_crc(save: bytearray, base: int, block: tuple[int, int, int, int]) -> None:
    offset, length, checksum_offset, checksum_mirror = block
    for save_base in (base, base + BACKUP_BASE):
        crc = crc16_ccitt(save[save_base + offset : save_base + offset + length])
        struct.pack_into("<H", save, save_base + checksum_offset, crc)
        struct.pack_into("<H", save, save_base + checksum_mirror, crc)


def verify_block_crc(save: bytes | bytearray, base: int, block: tuple[int, int, int, int]) -> bool:
    offset, length, checksum_offset, checksum_mirror = block
    for save_base in (base, base + BACKUP_BASE):
        actual = crc16_ccitt(save[save_base + offset : save_base + offset + length])
        expected = struct.unpack_from("<H", save, save_base + checksum_offset)[0]
        mirror = struct.unpack_from("<H", save, save_base + checksum_mirror)[0]
        if actual != expected or actual != mirror:
            return False
    return True


def build(source: Path, rom_path: Path, output: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Local test save not found: {source}")
    if not rom_path.is_file():
        raise FileNotFoundError(f"Matching clean source ROM not found: {rom_path}")
    original = source.read_bytes()
    if len(original) != SAVE_SIZE:
        raise ValueError(f"Expected a raw 512 KiB BW save, got {len(original)} bytes")

    game_code = rom_path.read_bytes()[12:16]
    expected_version = {b"IRBO": 20, b"IRAO": 21}.get(game_code)
    if expected_version is None:
        raise ValueError(f"Expected clean English BW ROM, found game code {game_code!r}")
    save_version = original[0x1941F]
    if save_version != expected_version:
        raise ValueError(
            f"Save version {save_version} does not match ROM version {expected_version}; "
            "refusing to convert or overwrite a different game's save"
        )

    # In BW1, map 7 is the Striaton Gym interior (map 6 is its parent city).
    map_id, x, z, y = checkpoint_position(rom_path, 7)
    save = bytearray(original)

    for save_base in (0, BACKUP_BASE):
        position_base = save_base + POSITION_BLOCK[0]
        struct.pack_into("<i", save, position_base + POSITION_OFFSETS["map_id"], map_id)
        struct.pack_into("<H", save, position_base + POSITION_OFFSETS["x"], x)
        struct.pack_into("<H", save, position_base + POSITION_OFFSETS["z"], z)
        struct.pack_into("<H", save, position_base + POSITION_OFFSETS["y"], y)

        # Reopen only the first-gym branch; preserve later-story progress.
        for flag_id in (0x597, 0x598, 0x599, 0x971, 0x972, 0x076, 0x077):
            set_flag(save, save_base, flag_id, False)
        misc_badge = save_base + MISC_BLOCK[0] + MISC_BADGES_OFFSET
        save[misc_badge] &= ~TRIO_BADGE_MASK

    for block in (POSITION_BLOCK, EVENT_WORK_BLOCK, MISC_BLOCK):
        update_block_crc(save, 0, block)
    update_block_crc(save, 0, CHECKSUM_BLOCK)
    for block in (POSITION_BLOCK, EVENT_WORK_BLOCK, MISC_BLOCK, CHECKSUM_BLOCK):
        if not verify_block_crc(save, 0, block):
            raise RuntimeError(f"CRC validation failed after editing block 0x{block[0]:05X}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(save)
    if output.read_bytes() == original:
        raise RuntimeError("Checkpoint output unexpectedly matches the source save")
    print(f"Created disposable checkpoint: {output}")
    print(f"  Game: {('Black' if expected_version == 20 else 'White')} (version {expected_version})")
    print(f"  Map ID {map_id} (Striaton Gym), entry coordinates X={x}, Y={y}, Z={z}")
    print("  Trio Badge and first-gym completion flags cleared")
    print("  Primary/backup CRC16 pairs verified; source save unchanged")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Local raw 512 KiB BW save")
    parser.add_argument("--rom", required=True, type=Path, help="Matching clean BW source ROM")
    parser.add_argument("--output", required=True, type=Path, help="Disposable checkpoint output path")
    args = parser.parse_args()
    try:
        build(args.source.resolve(), args.rom.resolve(), args.output.resolve())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
