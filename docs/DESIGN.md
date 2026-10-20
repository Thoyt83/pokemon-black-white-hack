# Design specification

## Project identity

This is a **vanilla-plus** rebalance of Pokémon Black and Pokémon White. It
should feel like a polished replay of the original games rather than a new game
using their engine.

Both versions will use one shared balance specification wherever their base
data allows it. Version-exclusive encounters, Opelucid's leader, and other
intentional Black/White differences remain intact.

## Non-negotiable rules

1. The complete pre-credits story uses only Unova Pokédex species.
2. Major trainers avoid duplicate species and duplicate evolutionary families
   wherever the available Unova roster permits it.
3. Difficulty comes primarily from coherent teams, sensible moves, useful held
   items, and improved AI flags—not large level jumps.
4. The level curve stays close to vanilla. Wild levels change only when
   playtesting shows that a trainer-level change has created a grinding gap.
5. The regional Pokédex, story progression, routes, version identity, and
   encounter character stay recognizably Black/White.
6. No commercial ROM, extracted copyrighted data, or rebuilt ROM is committed.
   Releases will contain patches and documentation only.

## Difficulty target

- A normal playthrough with a varied team should remain comfortable.
- Type advantage alone should help, but should not automatically win every boss
  fight.
- Grinding, EV training, breeding, and competitive movesets are never assumed.
- Ordinary trainers receive selective cleanup; rivals, Gym Leaders, Team Plasma
  bosses, the Elite Four, N, and Ghetsis receive hand-authored teams.
- Set mode, item bans, level caps, and Nuzlocke rules remain optional player
  choices rather than assumptions built into balance.

## Initial team direction

These are proposals to validate in game, not frozen final teams.

### Striaton Gym

The generic Lillipup is replaced by a second specialist Pokémon. Levels remain
12 and 14 for the first pass.

| Leader | Lead | Ace | Notes |
| --- | --- | --- | --- |
| Cilan | Sewaddle Lv. 12 | Pansage Lv. 14 | Clear Grass identity without using another starter. |
| Chili | Darumaka Lv. 12 | Pansear Lv. 14 | Strong thematic fit; Darumaka needs a restrained early moveset because of Hustle. |
| Cress | Tympole Lv. 12 | Panpour Lv. 14 | Clear Water identity and a fair early-game matchup. |

### First Elite Four challenge

Every member receives five Pokémon. The additions are from Unova, and no Elite
Four member repeats a species on their own team.

| Member | Fifth-member direction | Reasoning |
| --- | --- | --- |
| Shauntal | Zoroark | Illusion and deceptive ghost-story flavor compensate for Unova having only four fully evolved Ghost families. |
| Grimsley | Mandibuzz | A fully evolved Unova Dark type with a distinct defensive role. |
| Caitlin | Beheeyem | Completes the major fully evolved Unova Psychic roster without duplication. |
| Marshal | Emboar | A fully evolved Unova Fighting type with a distinct mixed attacking role. |

The four original members of each team will also be reviewed for moves, items,
AI, overlap, and role clarity. These fifth-member choices can change after the
full boss roster is reviewed.

## Whole-game review order

1. Gym Leaders and their Gym Trainers
2. Cheren and Bianca
3. Team Plasma commanders and mandatory story battles
4. Elite Four, N, and Ghetsis
5. Other mandatory trainers and obvious outliers
6. Post-game rematches and optional bosses
7. Wild encounters, only where progression or team availability needs support

## Quality-of-life policy

Good candidates are changes that remove friction without changing the game's
structure, such as practical single-player alternatives for trade evolutions,
clearer access to existing resources, and small interface or pacing fixes with
proven Gen V implementations.

The following are deliberately out of the first milestone:

- National Dex availability during the main story
- broad species/stat/type reworks
- Fairy type, later-generation moves, or later-generation battle mechanics
- removing Black/White version identity
- a new Amie/Refresh-style subsystem

Following Pokémon is a separate research milestone. It requires overworld
engine work, follower behavior, map/script integration, and a large sprite
asset set; it will not block the core rebalance.

Character customization is also a separate research milestone. The desired
version includes outfit shops in places such as Castelia City and salons that
offer hairstyles. A preset-based implementation is the preferred fallback if
independently selectable clothing and hair layers are impractical. See
`IDEAS.md` for the feature backlog and feasibility gates.

## Release model

The intended release artifacts are separate Black and White patches generated
from clean English ROM dumps. A manifest will record supported game codes,
input hashes, output hashes, patch format, and tool versions.

