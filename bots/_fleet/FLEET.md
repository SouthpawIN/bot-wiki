---
type: index
title: Fleet
updated: 2026-11-17
tags: [fleet, index]
---

# Fleet

Nine bots: eight per topic, plus `bot-wiki` (Klerik), which maintains the method
they all run on. Status legend: `live` (running now), `seeding` (skills written,
loops not yet armed), `blocked` (needs a human decision). Verified against every
`bots/*/BOT.md` on 2026-11-17: status and live-loop count are read from each
BOT.md's frontmatter and its own Loops table; "Blocked on" compresses that bot's
`## Needs from the operator`, never invents one. Nine rows read: 2 `live` at 1
loop each, 6 `seeding` at 0, `ssi` `blocked` at 0 — 12 declared loops, all 12 on
disk and none orphaned. Gates green at this commit: `verify_bots.py` 9 bots /
34 skills / 12 loops / 0 problems, `senter_agent . --json` parses, `pytest -q`
171 passed, 4 slow skipped. Both `live` loops are backed by real
cron jobs, not just declared state — `fleet-reconcile` at `0 6 * * *` and
`mesh-health` at `30 6 * * *`, both in the `default` profile with this wiki as
workdir. A loop whose BOT.md says `live` with no job behind it is an index bug.

| Bot | Callsign | Topic | Status | Live loops | Blocked on |
|---|---|---|---|---|---|
| [[bots/bot-wiki/BOT\|bot-wiki]] | Klerik | the method itself | live | 1 | — |
| [[bots/hermes/BOT\|hermes]] | Mesh | one Hermes across devices | live | 1 | device sign-in; phone OS; whether the MacBook keeps a local TurboFit node role |
| [[bots/turbofit/BOT\|turbofit]] | TurboSouth | TurboFit local inference + fit matrix | seeding | 0 | Darwin 125.3 GiB download decision; Arete on the unified ladder; an 8 GB card for the smoke test |
| [[bots/pocketshop/BOT\|pocketshop]] | Binder | MTG card flipping | seeding | 0 | printer IP; eBay token; fee + restock limits |
| [[bots/youtube/BOT\|youtube]] | Cutroom | Discord rants → YouTube | seeding | 0 | OBS output path; a 30-minute sample; channel identity |
| [[bots/ai-daw/BOT\|ai-daw]] | Riff | music generation plugin | seeding | 0 | GPU host for ACE-Step; plugin vs existing DAW UI |
| [[bots/anser/BOT\|anser]] | Anser | mod answer bot | seeding | 0 | X read credentials; channel list + mention policy |
| [[bots/kart-racer/BOT\|kart-racer]] | Apex | **Nous Racers** — Unity kart racer | seeding | 0 | repo visibility; Unity version; a controller to tune deadzones |
| [[bots/ssi/BOT\|ssi]] | Beacon | benefits paperwork (two-layer: public template + private profile) | blocked | 0 | private profile not yet created; documents in hand; any active denial |

## What is built, not just specified

| Bot | Working artifact | Proof |
|---|---|---|
| bot-wiki | `scripts/verify_bots.py`, `tools/publish_skills.py`, `fleet-reconcile` cron | 9 bots + the shared `sovthpaw-voice` and `wifi-scanner-control` skills; loop has run and committed |
| hermes | tailnet serve of the web app + 9 bot profiles | https://hermes-vps.tail6ff78b.ts.net:8443/ → 302 to Nous OAuth; `mesh-health` armed 06:30; `hermes profile list` shows all nine |
| turbofit | 62 catalog variants + recipes + manifest + matrix; `release-gate` specs campaign coverage | [PR #51](https://github.com/SouthpawIN/turbofit/pull/51), 936 tests pass; 1,165-cell campaign is the evidence ledger for every `measured` rung |
| pocketshop | `restock_ev.py` decision math | [PR #2](https://github.com/SouthpawIN/pocket-shop/pull/2), 13 tests |
| youtube | `scripts/cutroom.py` render + package | 27 tests on synthetic media |
| ai-daw | `plugin/` — six `daw_*` tools, adapters, renderer | 14 tests, real audio via ffmpeg; `stem-separation` skill written 2026-11-10 |
| anser | `scripts/corpus.py` fetch/cache/cite/refuse | 12 tests, import mode needs no credentials; `faq-distill` skill written 2026-11-11 |
| kart-racer | Unity project at [SouthpawIN/nrcu-kart](https://github.com/SouthpawIN/nrcu-kart): 7 C# scripts + 35-character roster | 8 roster tests; `tools/check_project.py` ok; **not yet compiled** — needs a Unity editor |
| ssi | `scripts/casefile.py` intake/deadlines/review/fill | 9 tests on synthetic AcroForm PDFs |

## Known drift

- `ai-daw/stem-separation`, `anser/faq-distill` and `turbofit/benchmark-rung`
  exist on disk but are not yet declared in their own Skills tables — only the
  owning bot edits its BOT.md. Filed as a fleet `[BOTS]` item on 2026-11-17;
  the validator counts them (34 skills) but no owning bot's published skill lists
  them, so the procedure exists and is unreachable from the bot that owns it.
- `ssi`: the program inventory the fleet queue still lists as missing to-do work
  is already written into `bots/ssi/BOT.md` (six programs, first form each,
  2026-11-07). The bot is now explicitly two-layer — public template plus
  `$HERMES_PRIVATE/ssi/profile.md` — so what still blocks specific operation is
  the operator creating that private profile, not missing writing.
- **Private-profile pattern.** Where a bot needs household/account/device facts,
  the repo carries only the shape and the loader contract; the values live at
  `$HERMES_PRIVATE/<bot>/` (defaulting to `~/.hermes/private/<bot>/`) and are
  never committed. `ssi` is the reference implementation
  (`bots/ssi/.system/profiles/README.md`); `pocketshop` applies it to seller
  identity and tokens, `hermes` to device names. A bot that hardcodes such a
  value in a tracked file is drifted, whatever its tests say.
- `hermes`: the 443 serve proxy points at `127.0.0.1:8788` (nothing listening),
  not the documented `8091`; `:9119` binds `0.0.0.0`. Recorded in its own log,
  unfixed.
- `bots/_fleet/skills/*` (`sovthpaw-voice`, `wifi-scanner-control`) **is now**
  installed by `tools/publish_skills.py` under `$HERMES_HOME/skills/fleet/<name>/`
  (2026-11-16), and `verify_bots.py` counts the fleet skills explicitly.
- `.system/` is gitignored, so queues and injections are per-clone state. The
  clone at `~/.hermes/wiki` carried none on 2026-11-12; the maintainer edits
  `~/work/agent-wiki` and mirrors them. Two clones, one queue, is a fork waiting
  to happen — worth making `.system/` tracked or fixing the mirroring.
- Both clones were corrupt again at the 2026-11-13 run: five zero-byte loose
  objects in `~/.hermes/wiki`, `HEAD` unreadable, no working tree. The documented
  repair (delete only 0-byte objects, `git fetch`, `git reset --mixed
  origin/main`, `git checkout -- .`) restored both with nothing lost —
  `43ea9aa` on `main`. The corruption is not a one-off: the cron job's workdir is
  the clone it is repairing, so an interrupted run damages its own checkout
  first. Nothing in the wiki can prevent that; only a worktree the job does not
  share (or a re-clone step at the start of the run) can.
- `pocketshop` ↔ `ssi` flatbed arbitration is one table in
  `bots/_fleet/skills/wifi-scanner-control` (07:00–19:00 cards, 19:00–07:00
  documents, `deadline-watch` outranks both). Published to
  `$HERMES_HOME/skills/fleet/wifi-scanner-control/` as of 2026-11-16.

## Cross-bot dependencies

- `hermes` (Mesh) must land before `anser` and `ssi` are pleasant: both want to
  be reachable from the phone.
- `pocketshop` and `ssi` share one physical asset: the Wi-Fi printer/scanner.
  `pocketshop` gets it for card flatbeds, `ssi` for documents. Neither may
  reconfigure it without telling the other (queue item in both). The runtime
  contract between them is `bots/_fleet/skills/wifi-scanner-control`.
- `turbofit` computes the local hardware budget that `ai-daw` and `youtube`
  want for local inference. TurboSouth publishes the matrix; the other two read it.

## Standing rules

- Public output says **sovthpaw**, never the operator, never Southpaw.
- Nothing spends money without a hold point satisfied.
- Every bot's `## Log` is append-only and newest-first.
