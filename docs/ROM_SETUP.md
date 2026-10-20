# Local ROM setup

The project needs clean, personally dumped English copies of both games. Do not
commit or upload them to GitHub.

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

