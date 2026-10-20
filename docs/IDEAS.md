# Feature backlog

This file records ideas without promising them for the first release. Features
advance only after a technical prototype works in both Black and White without
damaging saves, maps, story scripts, or version identity.

## Core release

- Hand-authored major trainer rebalance
- Selective ordinary-trainer cleanup
- Five-member Elite Four teams for the first challenge
- Main-story Unova-only opponent roster
- Encounter and level-curve adjustments only where playtesting requires them
- Small, proven quality-of-life improvements

## Character customization

**Desired experience:** add clothing shops in appropriate cities—especially
Castelia—and salons where the player can purchase or select hairstyles.

**Preferred implementation:** a small set of curated appearances that preserve
the visual style of Hilbert and Hilda. Shops or salons would unlock/select a
complete appearance preset, with clear previews and prices appropriate to game
progression.

**Stretch implementation:** independently selectable outfits and hairstyles.
This is substantially harder because the original game does not provide a
layered avatar system.

Any implementation must account for all relevant player representations,
including normal overworld movement, running, biking, surfing, fishing, battle
backsprites, the Trainer Card, and scripted scenes. It also needs a safe place
in the save data for the active selection and flags for purchased options.

**Feasibility gate:** first prove that one alternate preset can be selected,
saved, reloaded, and displayed consistently in both games. Only then design
shops, salons, prices, unlock schedules, and additional art.

**Fallback:** if runtime selection is unsafe, offer a few separately generated
patch variants that replace the protagonist's appearance globally. This would
not provide in-game shops, but it would still provide player choice.

## Following Pokémon

Research after the core trainer/encounter pipeline is stable. A viable prototype
must handle follower spawning, collision, warps, doors, stairs, map transitions,
bikes, surfing, scripted scenes, and a representative sprite set.

## Amie/Refresh-style interaction

Exploratory only. A full new interaction subsystem would require extensive UI,
animation, input, save-data, and gameplay-effect work. Smaller friendship-based
interactions using existing NPC/script systems may be considered if they fit the
vanilla experience.

## Backlog rules

- New features cannot delay a stable core rebalance release.
- Both Black and White must receive equivalent support.
- Features should use original project assets or properly licensed assets only.
- No feature may require distributing a commercial ROM or copyrighted extracted
  game data.
