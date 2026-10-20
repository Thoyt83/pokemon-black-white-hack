"""ROM-free integrity checks for the hand-authored boss team proposals."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = json.loads((ROOT / "data/design/boss_teams.json").read_text(encoding="utf-8"))
REFERENCES = json.loads((ROOT / "data/reference/gen5_ids.json").read_text(encoding="utf-8"))


class BossTeamDesignTests(unittest.TestCase):
    def test_design_declares_vanilla_plus_story_rules(self) -> None:
        self.assertEqual(DESIGN["status"], "proposal")
        self.assertEqual(DESIGN["shared_rules"]["pre_credits_species_pool"], "unova")
        self.assertTrue(DESIGN["shared_rules"]["avoid_duplicate_species"])
        self.assertTrue(DESIGN["shared_rules"]["avoid_duplicate_evolutionary_families"])

    def test_battle_keys_and_trainer_ids_are_unique(self) -> None:
        keys = [battle["key"] for battle in DESIGN["battles"]]
        self.assertEqual(len(keys), len(set(keys)))
        trainer_ids = [
            battle["trainer_id"]
            for battle in DESIGN["battles"]
            if "trainer_id" in battle
        ]
        self.assertEqual(len(trainer_ids), len(set(trainer_ids)))

    def test_striaton_leaders_have_thematic_unova_parties(self) -> None:
        expected = {
            "striaton_cilan": ("Sewaddle", "Pansage"),
            "striaton_chili": ("Darumaka", "Pansear"),
            "striaton_cress": ("Tympole", "Panpour"),
        }
        battles = {battle["key"]: battle for battle in DESIGN["battles"]}
        self.assertEqual(set(expected) & set(battles), set(expected))
        for key, species in expected.items():
            with self.subTest(leader=key):
                battle = battles[key]
                self.assertEqual(battle["phase"], "main_story")
                self.assertEqual(tuple(member["species"] for member in battle["party"]), species)
                self.assertNotIn("Lillipup", [member["species"] for member in battle["party"]])
                self.assertEqual(len({member["species"] for member in battle["party"]}), len(battle["party"]))

    def test_elite_four_first_encounter_additions_are_distinct_unova_species(self) -> None:
        additions = [
            battle
            for battle in DESIGN["battles"]
            if battle["key"].startswith("elite_four_")
            and battle["phase"] == "main_story"
        ]
        self.assertEqual(len(additions), 4)
        species = [battle["append"]["species"] for battle in additions]
        self.assertEqual(len(species), len(set(species)))
        for name in species:
            with self.subTest(species=name):
                species_id = REFERENCES["species"][name]
                self.assertGreaterEqual(species_id, 494)
                self.assertLessEqual(species_id, 649)

    def test_all_proposed_species_and_moves_have_reference_ids(self) -> None:
        for battle in DESIGN["battles"]:
            members = battle.get("party", [])
            if "append" in battle:
                members = [*members, battle["append"]]
            for member in members:
                name = member["species"]
                with self.subTest(battle=battle["key"], species=name):
                    self.assertIn(name, REFERENCES["species"])
                    level = member["level"]
                    self.assertGreaterEqual(level, 1)
                    self.assertLessEqual(level, 100)
                    moves = member.get("moves", [])
                    self.assertLessEqual(len(moves), 4)
                    for move in moves:
                        self.assertIn(move, REFERENCES["moves"])


if __name__ == "__main__":
    unittest.main()
