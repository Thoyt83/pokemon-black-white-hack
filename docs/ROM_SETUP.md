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
   - `BW_CHECKPOINT_DIR`: directory containing optional BizHawk `.State`
     checkpoints for leader battle-start tests.
   - `BW_BLACK_SAVE` and `BW_WHITE_SAVE`: paths to matching, local raw saves
     (512 KiB each). Only the selected game's save is required for a gym-entry
     checkpoint test. Saves stay outside the repository and are never uploaded.
   - `BIZHAWK_EXE`: full path to `EmuHawk.exe`.
4. Install project dependencies and build the local patch with
   `python -m pip install -r requirements.txt` and
   `python scripts/build_striaton.py`. For each game/leader combination, use
   the resulting patched Striaton ROM in BizHawk,
   enter the corresponding Gym battle, and save a BizHawk state at the battle
   start if you want a leader battle-start test. Name them `black-cilan.State`, `black-chili.State`,
   `black-cress.State`, `white-cilan.State`, `white-chili.State`, and
   `white-cress.State`. Keep these files in the local checkpoint directory;
   do not add them to Git.
5. In GitHub, open Actions → `Local ROM TAS smoke test` → Run workflow and
   choose a game and `gym-entry` to generate a disposable save checkpoint and
   verify it loads into the gym. Choose a leader to run the separate battle-start
   TAS from a local `.State` file. Download the screenshot artifact to inspect
   the result.

The workflow's gym-entry path builds the save checkpoint from a local save and
restores the runner's prior BizHawk SaveRAM afterward. Leader battle-start paths
still use supplied savestates. Both are emulator smoke tests and visual evidence,
not an automated judgment of game balance. Artifacts include gameplay screenshots
and are publicly accessible because the repository is public.

## Create the verified Striaton Gym-entry save

For a local test without a pre-existing BizHawk `.State`, create a disposable
raw-save checkpoint from a save that matches the ROM version:

```powershell
python -m pip install -r requirements.txt
python scripts/create_test_checkpoint.py `
  --source "C:\path\to\your-matching-save.sav" `
  --rom "roms\source\pokemon_white.nds" `
  --output "build\rom-test\white-striaton-gym.sav"
```

The generator confirms the save's Black/White version before editing it. It
places the player at Striaton Gym (map 7, entry X=5, Y=4, Z=0), clears the first
gym's completion flags and Trio Badge bit, and updates both in-block and mirrored
CRC16 fields in the primary and backup save copies. It never edits the source
save. This exact White checkpoint was accepted by BizHawk and visibly loaded
the player into the gym interior.

Copy the generated `.sav` to BizHawk's `NDS\SaveRAM` entry for the patched ROM,
preserving any existing file first. Launch the patched ROM with
`tests/bizhawk_save_checkpoint_verify.lua`; set `BW_TAS_OUTPUT_DIR` to a local
output directory. The script advances with A through the intro and captures
only three milestones: the Continue card, C-Gear prompt, and loaded gym scene.
The `gym-entry` GitHub Action uses the same generator and restores the runner's
previous SaveRAM after the run. Leader battle-start tests still use separate
`.State` files until the battle-entry input sequence is automated.

For a visible manual launch that leaves BizHawk open in the gym, use
`tests/bizhawk_launch_in_striaton.lua` with the patched ROM after the generated
checkpoint has been copied into its SaveRAM slot. It advances the intro and
wireless prompts, then returns the emulator to normal speed without exiting.

