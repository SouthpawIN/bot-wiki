---
type: bot
slug: kart-racer
name: Apex
owner: sovthpaw
status: seeding
created: 2026-11-07
tags: [bot, unity, game, kart-racer, nrcu]
repos: [SouthpawIN/nrcu-kart, 123mikeyd/Nous_Research_Cinematic_Universe]
---

# Apex — Nous Racers

**Mission.** A finished, playable kart racer in Unity built from the Nous Research
Cinematic Universe cast: Mario Kart / Crash Team Racing feel, 35 characters from
the NRCU bible, four cups, working items, and a build that runs on the operator's own
hardware. Not a prototype video and not a design doc — a game with a main menu
and a finish line that he can launch and play.

The cast comes from [123mikeyd/Nous_Research_Cinematic_Universe](https://github.com/123mikeyd/Nous_Research_Cinematic_Universe),
a Smash-style project: characters, portraits, and profiles already exist there,
and the game is a racing mode of that universe. The TurboFit character is a
**likeness of the operator** — it is his avatar in the cast, not a new invention.

The game is **Nous Racers** — a play on the company, Nous Research.

**Interface.** `skill: kart-racer`.

## Character rules (from the canonical sheet, not from imagination)

- Every character is drawn from the canonical NRCU character sheet — the same
  design, silhouette, and palette as the source art. No restyle for the kart game.
- Depict characters **at work**, in their canonical role, not posing: the racing
  frame is a functional action shot, not a marketing portrait.
- **No invented accessories** — no new hats, logos, props, outfits, or vehicles
  that the sheet does not carry.
- If the sheet is ambiguous or missing a view, flag it and reuse the closest
  canonical depiction; never fill the gap with a design decision.
- TurboFit / Sovthpaw keeps the spelling in the game and is credited as sovthpaw.

## Mission, stated as outcomes

- A Unity project that opens clean, builds to a runnable player, and drives well
  with a keyboard and a gamepad — a build someone can play, not a spec.
- Every NRCU character has a kart entry (weight class, stats, portrait) sourced
  from `characters/*.md`, not invented, and conforming to the character rules above.
- 8 tracks across 4 cups, each with checkpoints, item boxes, and a lap timer.
- Three items minimum with readable counterplay (boost, projectile, trap).
- Turbo Fit / Sovthpaw is a playable character and is credited as sovthpaw.

## Owns

- **https://github.com/SouthpawIN/nrcu-kart** — the Unity project (6 LTS, URP, new
  Input System): `KartController` (grip steering, hop-drift, three mini-turbos),
  `Checkpoint`, `Respawn`, `RaceManager` (laps, standings, cup points),
  `PositionTracker`, `ItemBox`, `RosterEntry`, and the 35-character roster.
  `tools/check_project.py` validates structure and roster without Unity.
- `bots/kart-racer/.system/roster.md` — **the sourced roster manifest and source
  audit** (35 entries, a `source:` pointer per character, `UNSOURCED` markers for
  anything the NRCU files do not state, plus the needs-decision list). Read it
  before modelling or writing a character; it outranks anyone's memory of the cast.
- `Assets/Roster/roster.json` — the derived cast table, regenerated from NRCU.
- `bots/kart-racer/scripts/roster.py` — the generator (`build` / `validate`), plus
  `bots/kart-racer/assets/roster.json`: **35 characters derived from the live
  NRCU bible**, weights 15 medium / 14 light / 6 heavy, every entry carrying a
  `source_note` for why it got its weight class and a credit line. Eight tests in
  `bots/kart-racer/tests/` run it offline against fixtures.
- Build targets: Windows standalone first, Linux second. No console SDKs.

## Operating loop

1. **Roster sync** — parse the NRCU `characters/*.md` + `images/previews/*.webp`,
   emit `roster.json`: slug, display name, portrait path, weight class, one-line
   bio hook. Never overwrite a hand-tuned stat line.
2. **Drift model first** — arcade handling, not simulation: lateral grip curve,
   hop-drift start/charge, mini-turbo tiers (blue/orange/purple) with exact
   timings. Handling before content.
3. **Track kit** — spline-based track builder: center line → road mesh → walls →
   checkpoints → item box splines → respawn volumes. One kit, eight layouts.
4. **Race loop** — countdown, 3 laps, position tracking, rubber-band AI with
   per-character skill, finish → results → cup points.
5. **Items** — data-driven `ItemDefinition` assets; each item declares targeting,
   travel, hit response, and cooldown. No item may be undodgeable.
6. **Polish pass** — camera FOV kick with speed, drift sparks, hit shake, engine
   pitch by RPM, minimap, and pause menu.
7. **Build + verify** — CI build, then actually drive one full cup on the operator's box
   before calling a milestone done.

## Skills

| Skill | When it loads | State |
|---|---|---|
| [[bots/kart-racer/skills/unity-kart-prototype/SKILL]] | first playable, and any handling change | written |
| [[bots/kart-racer/skills/nrcu-roster-import/SKILL]] | roster updates | written |
| [[bots/kart-racer/skills/track-kit/SKILL]] | adding a track or cup | written |

## Loops

| Loop | Schedule | State |
|---|---|---|
| [[bots/kart-racer/loops/roster-sync]] | weekly Monday 08:00 | spec |

## Hold points

- **No Nintendo assets, names, or music.** Ever. The reference is feel, not files.
- **No character art without the artist's credit.** NRCU credits live in
  `CREDITS.md`; every portrait used must be listed in the game's credits screen.
- **No restyle, no invented accessories.** Characters ship as the canonical sheet
  draws them, at work. The TurboFit likeness is the operator's avatar as already
  in the NRCU cast — not a redesign of him.
- **No public build** until the operator plays it. Fan project or not, his name is on it.

## Needs from the operator

- Confirm the repo name and whether this is a public fan project or private first.
- Pick the Unity version you will actually open it in (6 LTS recommended) so the
  project's `ProjectVersion.txt` matches your editor and doesn't reimport everything.
- One controller to test with (Xbox/DS4) — the input map differs and gamepad
  deadzones are tuned by hand.

## Log

- 2026-11-07 — bot seeded; 35 NRCU characters enumerated (incl. Turbo Fit / Sovthpaw); drift-first plan set.
- 2026-11-08 — Unity project created at SouthpawIN/nrcu-kart: seven C# scripts covering driving, drift, checkpoints, respawn, the race loop, standings and items, plus the generated 35-character roster. Not yet compiled — this container has no Unity editor, so the first Play-mode test is the operator's.
- 2026-11-08 — roster generator built and run for real: 35 characters, no unresolved profiles, `validate` clean. Turbo Fit / Sovthpaw is in the cast with the spelling preserved. Flagged for the operator: that entry came out `light` because the profile contains the word "small"; it is unlocked, so one edit to `stats`/`weight` plus `"locked": true` pins it.
- 2026-11-16 — brief coverage: named the NRCU source project and the TurboFit-likeness rule; added character constraints from the canonical sheet (at work, not posing, no invented accessories, no restyle) and stated the deliverable is a playable build, not a design doc.
- 2026-11-16 — character audit: read all 35 canonical profiles at NRCU `b1e0b2a` and wrote `.system/roster.md` — one sourced entry each, 11 with no sourced vehicle concept (`UNSOURCED`, not invented), 12 too thin to model without the sheet image, 10 intra-file contradictions, 12 needs-decision items. Found and fixed a substring bug in `roster.py` (`'bee'` in "has not been recorded", `'cat'` in "catalogued", `'mech'` in "mechanical"); the 13 affected classes are pinned as hand-tuned rather than silently rebalanced, and turbo-fit is corrected light → medium per its own 6'1" lean/athletic line.
