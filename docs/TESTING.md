# Testing Log

## ROM-free GitHub Actions checks

The `ROM-free project checks` workflow runs on pushes, pull requests, and
manual dispatch. It validates the current hand-authored team proposals against
the project rules and Gen V reference IDs, then uploads a PNG team report as a
30-day Actions artifact.

These cloud checks do not include commercial ROMs and do not simulate actual
gameplay, battle AI, graphics, or emulator compatibility. ROM build checks
remain local because the clean Black and White dumps must stay on the owner's
machine. Emulator screenshots and save-based battle testing remain a separate
manual smoke test.

## Local-ROM TAS smoke tests

The `Local ROM TAS smoke test` workflow is manual-only and targets a dedicated
Windows self-hosted runner. It builds the Striaton patches from the runner's
local clean ROMs, launches BizHawk's melonDS core with a local battle savestate,
plays a short scripted input sequence, and uploads battle screenshots as
Actions artifacts. It never copies source ROMs or savestates into the checkout
or uploads them. Because this repository is public, the runner job is restricted
to manual dispatch from `main` by the repository owner and is not attached to
push or pull-request events. The screenshot artifacts themselves are public.

See [ROM_SETUP.md](ROM_SETUP.md#tas-runner-setup) for the one-time runner and
checkpoint setup. The job cannot run until that Windows runner is online and
each selected checkpoint exists locally.

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

