# Local ROM setup

The project needs clean English ROM dumps that you are legally entitled to use.
Do not commit or upload them to GitHub.

Place the files in `roms/source/`. The suggested names are:

```text
roms/source/pokemon_black.nds
roms/source/pokemon_white.nds
```

Other filenames are accepted; the validator identifies each game from its
Nintendo DS cartridge header.

Then run:

```powershell
python scripts/verify_roms.py
```

The validator checks the Nintendo DS header, distinguishes English Black
(`IRBO`) from English White (`IRAO`), reports the SHA-1 hashes, and recognizes
known clean full-dump hashes. Unknown hashes are reported for review instead of
being silently accepted as the build baseline.

The source and working ROM directories are ignored by Git. Final distribution
will use patch files rather than modified ROM images.

# TAS runner setup

The optional `Local ROM TAS smoke test` GitHub Action runs only on a Windows
self-hosted runner. GitHub-hosted runners cannot see ROMs stored on your PC, and
the workflow intentionally does not upload ROMs or saves.

1. Install a current BizHawk release on the runner PC. BizHawk's melonDS core is
   used for scripted frame stepping and screenshots; the existing standalone
   melonDS 1.1 app does not provide this workflow's Lua automation interface.
2. Add a repository self-hosted runner labeled `rom-test` and run it
   interactively in your logged-in Windows session (not as a background
   service). The repository is public, so keep the runner dedicated to this
   repo and do not enable pull-request or push triggers for the ROM workflow.
3. Set these machine environment variables for the runner account, then restart
   the runner process:
   - `BW_ROM_SOURCE_DIR`: directory containing exactly one clean English Black
     ROM and one clean English White ROM (`.nds` files).
   - `BW_CHECKPOINT_DIR`: directory containing BizHawk `.State` checkpoints.
   - `BIZHAWK_EXE`: full path to `EmuHawk.exe`.
4. Install project dependencies and build the local patch with
   `python -m pip install -r requirements.txt` and
   `python scripts/build_striaton.py`. For each game/leader combination, use
   the resulting patched Striaton ROM in BizHawk,
   enter the corresponding Gym battle, and save a BizHawk state at the battle
   start. Name them `black-cilan.State`, `black-chili.State`,
   `black-cress.State`, `white-cilan.State`, `white-chili.State`, and
   `white-cress.State`. Keep these files in the local checkpoint directory;
   do not add them to Git.
5. In GitHub, open Actions → `Local ROM TAS smoke test` → Run workflow and
   choose a game and leader. Download the resulting screenshot artifact to
   inspect the scripted battle sequence.

The workflow runs a fixed, repeatable sequence from a supplied savestate. It is
an emulator smoke test and visual evidence, not an automated judgment of game
balance. Artifacts include gameplay screenshots and are publicly accessible
because the repository is public.

