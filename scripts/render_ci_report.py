#!/usr/bin/env python3
"""Render a visual summary of ROM-free CI checks and current team proposals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "data" / "design" / "boss_teams.json"


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "ci" / "team-report.png")
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    battles = design["battles"]
    striaton = [battle for battle in battles if battle["key"].startswith("striaton_")]
    elite_four = [battle for battle in battles if battle["key"].startswith("elite_four_")]

    width = 1200
    row_height = 74
    height = 270 + row_height * (len(striaton) + len(elite_four))
    image = Image.new("RGB", (width, height), "#101923")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((32, 24, width - 32, 138), radius=20, fill="#1b2a38", outline="#3c5b70", width=2)
    draw.text((58, 42), "UNOVA VANILLA+ | CI TEAM REPORT", font=font(28), fill="#f5f8fb")
    draw.text((60, 88), "ROM-free design checks passed — no game ROM or gameplay simulator used", font=font(17), fill="#a8c2d4")

    y = 166
    draw.text((48, y), "STRIATON GYM PROPOSALS", font=font(20), fill="#72d4c0")
    y += 38
    for battle in striaton:
        leader = battle["key"].replace("striaton_", "").title()
        members = "  /  ".join(f"{member['species']} Lv. {member['level']}" for member in battle["party"])
        draw.rounded_rectangle((44, y, width - 44, y + 58), radius=12, fill="#1b2a38")
        draw.text((64, y + 17), leader, font=font(18), fill="#f5f8fb")
        draw.text((300, y + 17), members, font=font(18), fill="#d4e4ed")
        y += row_height

    y += 3
    draw.text((48, y), "ELITE FOUR — FIRST ENCOUNTER ADDITIONS", font=font(20), fill="#f2c36b")
    y += 38
    for battle in elite_four:
        member = battle["append"]
        member_name = battle["key"].replace("elite_four_", "").replace("_initial", "").title()
        draw.rounded_rectangle((44, y, width - 44, y + 58), radius=12, fill="#1b2a38")
        draw.text((64, y + 17), member_name, font=font(18), fill="#f5f8fb")
        draw.text((400, y + 17), f"+ {member['species']} Lv. {member['level']}", font=font(18), fill="#d4e4ed")
        y += row_height

    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"Visual report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
