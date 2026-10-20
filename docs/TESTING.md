# Testing Log

## 2026-10-19 — Striaton milestone

Environment: melonDS 1.1 for Windows x86_64.

### Automated checks

- Both source ROMs match recognized clean-dump SHA-1 hashes.
- Both generated ROMs remain exactly 268,435,456 bytes.
- Each build changes 25 bytes inside `a/0/9/3` (trainer party data).
- No bytes outside the intended trainer NARC differ from either source ROM.
- The preserved elemental-monkey ace records match the vanilla data.

### Emulator smoke test

- Pokémon Black build boots successfully and runs its intro at 60/60 FPS.
- Pokémon White build boots successfully and runs its intro at 60/60 FPS.
- No boot-time error, crash, or malformed startup graphics was observed.

### Still required

- Play from a fresh save, or use a compatible save near Striaton City.
- Trigger all three possible leader battles and confirm the lead Pokémon,
  levels, moves, animations, and battle completion.
- Evaluate whether each matchup feels like a modest vanilla-plus challenge.

