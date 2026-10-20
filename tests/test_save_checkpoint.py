from __future__ import annotations

from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from scripts import create_test_checkpoint as checkpoint


class SaveCheckpointTests(unittest.TestCase):
    def test_build_edits_disposable_save_and_recalculates_both_crc_copies(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.sav"
            rom = root / "white.nds"
            output = root / "checkpoint.sav"

            original = bytearray(checkpoint.SAVE_SIZE)
            original[0x1941F] = 21
            original[checkpoint.MISC_BLOCK[0] + checkpoint.MISC_BADGES_OFFSET] |= checkpoint.TRIO_BADGE_MASK
            for flag_id in (0x597, 0x598, 0x599, 0x971, 0x972, 0x076, 0x077):
                flag_offset = checkpoint.EVENT_FLAGS_BASE + flag_id // 8
                original[flag_offset] |= 1 << (flag_id % 8)
                backup_flag_offset = checkpoint.BACKUP_BASE + flag_offset
                original[backup_flag_offset] |= 1 << (flag_id % 8)
            original[checkpoint.BACKUP_BASE + checkpoint.MISC_BLOCK[0] + checkpoint.MISC_BADGES_OFFSET] |= checkpoint.TRIO_BADGE_MASK
            source.write_bytes(original)
            rom.write_bytes(b"\0" * 12 + b"IRAO")

            with patch.object(checkpoint, "checkpoint_position", return_value=(7, 5, 0, 4)):
                checkpoint.build(source, rom, output)

            generated = output.read_bytes()
            self.assertEqual(source.read_bytes(), bytes(original))
            self.assertNotEqual(generated, bytes(original))

            for save_base in (0, checkpoint.BACKUP_BASE):
                position = save_base + checkpoint.POSITION_BLOCK[0]
                self.assertEqual(struct.unpack_from("<i", generated, position + 0x80)[0], 7)
                self.assertEqual(struct.unpack_from("<H", generated, position + 0x86)[0], 5)
                self.assertEqual(struct.unpack_from("<H", generated, position + 0x8A)[0], 0)
                self.assertEqual(struct.unpack_from("<H", generated, position + 0x8E)[0], 4)
                self.assertEqual(generated[save_base + 0x21204] & checkpoint.TRIO_BADGE_MASK, 0)
                for flag_id in (0x597, 0x598, 0x599, 0x971, 0x972, 0x076, 0x077):
                    flag_offset = save_base + checkpoint.EVENT_FLAGS_BASE + flag_id // 8
                    self.assertEqual(generated[flag_offset] & (1 << (flag_id % 8)), 0)

            for block in (
                checkpoint.POSITION_BLOCK,
                checkpoint.EVENT_WORK_BLOCK,
                checkpoint.MISC_BLOCK,
                checkpoint.CHECKSUM_BLOCK,
            ):
                self.assertTrue(checkpoint.verify_block_crc(generated, 0, block))

    def test_build_rejects_save_from_other_game(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.sav"
            rom = root / "black.nds"
            output = root / "checkpoint.sav"
            save = bytearray(checkpoint.SAVE_SIZE)
            save[0x1941F] = 21
            source.write_bytes(save)
            rom.write_bytes(b"\0" * 12 + b"IRBO")

            with self.assertRaisesRegex(ValueError, "does not match ROM version"):
                checkpoint.build(source, rom, output)


if __name__ == "__main__":
    unittest.main()
