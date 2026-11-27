---
type: index
title: Fleet
updated: 2026-11-25
tags: [fleet, index]
---

# Fleet

Ten bots: nine per topic, plus `bot-wiki` (Klerik), which maintains the method
they all run on. Status legend: `live` (running now), `seeding` (skills written,
loops not yet armed), `blocked` (needs a human decision), `paused` (archived —
kept, not deleted). Verified against every `bots/*/BOT.md` on 2026-11-25: status
and live-loop count are read from each BOT.md's frontmatter and its own Loops
table; "Blocked on" compresses that bot's `## Needs from the operator`, never
invents one. Ten rows read against ten BOT.md files and all ten agree: 2 `live`
at 1 loop each, 7 `seeding` at 0, `ssi` `blocked` at 0. Loop bookkeeping holds:
**14 loops declared, 14 on disk**, none orphaned and none missing — two `live`,
the other twelve `spec`/`ready`. Four of the 41 skills are still undeclared in
their owner's Skills table (named under Known drift), which the validator counts
rather than hides.
`ssi` now stands at **18 days blocked** (seeded 2026-11-07) with no human reply,
so the demote-to-`paused` rule is overdue — but the row is Beacon's BOT.md, which
only its owner edits, so the demotion is owed as a one-line owner edit rather
than applied from here; `bot-archive` is the format that edit follows.
Gates green at this commit: `verify_bots.py` 10 bots / 41 skills / 14 loops / 0
problems, `senter_agent . --json` parses (98 documents, 99 proposals), `pytest`
218 passed with 5 slow skipped, privacy gate PASS. Loaders exist in **two** install roots and both are now current:
`$HERMES_HOME/skills` (`/opt/data/skills` under cron — the root this runtime
reads) and `~/.hermes/skills` (what a session started with the default home
would read). `tools/publish_skills.py` defaults to `$HERMES_HOME`, so the
2026-11-24 run refreshed the first and left the second at 2026-11-23 21:08;
rendering into both, then byte-diffing, is the check — an mtime comparison
across roots proved nothing, and the mtime rule written here last run is
replaced. A loader does not render its BOT.md's `## Log`, so today's only real
loader change was `bot-bot-wiki` ("Nine projects" → ten). A published skill
older than its BOT.md is drift; one that is missing
is a bot that does not exist from a session's side. Both `live` loops are backed
by active cron jobs, not just declared state — `fleet-reconcile` at `0 6 * * *`
(last run 2026-11-24 15:26) and `mesh-health` at `30 6 * * *` (last run
2026-11-25 23:01, ok), both in the `default` profile with this wiki as workdir,
4 jobs there. A loop whose BOT.md says `live` with no job behind it is an index
bug. Both fired today only as catch-up dispatches (`fleet-reconcile` 17h late,
`mesh-health` 16h 30m late), so a green `last run: ok` line does not mean the
schedule held.

**One standing row closed as superseded; nothing else was claimable** (verified
2026-11-24, re-verified 2026-11-25 oldest first: same classes, no row became
claimable). The 28 open `[ ]` rows across the eleven queue files
sorted into five classes and only these: **12 loop arms** (ai-daw
`engine-watch`, anser `corpus-refresh`, kart-racer `roster-sync`, ssi
`deadline-watch` and fleet `ssi:deadline-watch-arm`, pocketshop `ev-discovery`
and `sale-watch`, turbofit `artifact-audit` and `release-gate`, youtube
`nightly-ingest` and `weekly-cut`, resume `metrics-sweep`), which this loop may
not perform; **4 skill-gated** (`kart-racer/item-system`, `ssi/appeal-packet`,
youtube `broll-library`, resume `interview-prep`), each waiting on an artifact
that does not exist yet — a first playable cup, a first denial, a first render,
a first live application; **2 owner BOT.md edits** (`skills-declare-orphans`,
`kart-racer:needs-decision`), filed as pointers because only the owning bot
declares; **9 operator-gated** (`ssi:private-profile` plus Beacon's documents,
Riff's GPU host and `second-engine`, Anser's channels, TurboSouth's Darwin
quant, Binder's `amazon-path`, Mesh's `surface-attach`, Folio's unconfirmed
metrics); and **1 standing row this loop owned** — bot-wiki's "promote bots to
`live` as their blockers clear", whose named premise (PR #51) has been merged
since 2026-11-08. That row was audited against the `bot-promote` gate this run
and closed as superseded, **not** as promotion: no bot is promotable, because
gate step 1 — its loop run by hand end-to-end once, with output the operator can
look at — has been met by none. Every loop outside the two `live` ones is still
`spec`/`ready` with no cron job, and hermes is already `live`, so "promote as
blockers clear" has no subject left to act on; the recurring half is the
`bot-promote` procedure plus the `Blocked on` column below. 27 open rows remain
(24 in this clone's ten queues plus Folio's three, now mirrored here — see Known
drift), each held by one of the classes above. The operator's asks are named per bot in
each `## Needs from the operator` and compressed into the `Blocked on` column;
`$HERMES_PRIVATE/ssi/profile.md` is still absent on 2026-11-25 (while
`$HERMES_PRIVATE/resume/profile.md` exists, which is why Folio is `seeding` with
specific operation unblocked and its loop unarmed). This page's 2026-11-25
re-check writes one injection — Folio's queue was missing from the working
clone, so its three rows were invisible to a reconcile run from there — and
does not re-state the ssi ask that `bot-archive` phrased once.
`kart-racer`'s character audit closed 2026-11-18: `.system/roster.md` carries
one sourced entry per canonical NRCU character (35), 71 `[[UNSOURCED]]` markers
and 12 needs-decision items, so the proof cell reads the audit rather than only
the test count.

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
| [[bots/resume/BOT\|resume]] | Folio | one client's résumé: ledger, rewrite, tailoring | seeding | 0 | metric sweep not armed; unconfirmed facts list with the client |

## What is built, not just specified

| Bot | Working artifact | Proof |
|---|---|---|
| bot-wiki | `scripts/verify_bots.py`, `tools/publish_skills.py`, `fleet-reconcile` cron; `bot-archive` for the lifecycle's other end | 10 bot loaders + the shared `sovthpaw-voice` and `wifi-scanner-control` skills, re-rendered 2026-11-24; loop has run and committed |
| hermes | tailnet serve of the web app + 9 bot profiles | https://hermes-vps.tail6ff78b.ts.net:8443/ → 302 to Nous OAuth; `mesh-health` armed 06:30; `hermes profile list` shows all ten |
| turbofit | 62 catalog variants + recipes + manifest + matrix; `release-gate` specs campaign coverage | [PR #51](https://github.com/SouthpawIN/turbofit/pull/51), 936 tests pass; 1,165-cell campaign is the evidence ledger for every `measured` rung |
| pocketshop | `restock_math.py` + `trading_gate.py` decision math; `savings-markets` skill | 35 tests in `bots/pocketshop/tests/`; [PR #2](https://github.com/SouthpawIN/pocket-shop/pull/2) for the original EV path |
| youtube | `scripts/cutroom.py` render + package | 27 tests on synthetic media |
| ai-daw | `plugin/` — six `daw_*` tools, adapters, renderer | 28 tests (14 plugin + 14 engines), real audio via ffmpeg; `stem-separation` skill written 2026-11-10 |
| anser | `scripts/corpus.py` fetch/cache/cite/refuse | 12 tests, import mode needs no credentials; `faq-distill` skill written 2026-11-11 |
| kart-racer | Unity project at [SouthpawIN/nrcu-kart](https://github.com/SouthpawIN/nrcu-kart): 7 C# scripts + 35-character roster; `.system/roster.md` — the source audit, one entry per canonical NRCU character, 71 `[[UNSOURCED]]` markers, 12 needs-decision items | 9 roster tests; `tools/check_project.py` ok; **not yet compiled** — needs a Unity editor |
| ssi | `scripts/casefile.py` intake/deadlines/review/fill | 9 tests on synthetic AcroForm PDFs |
| resume | `scripts/resume.py` parse/lint/ledger/keywords/render | 13 tests on synthetic résumés; a real master linted to 0 errors and rendered to .docx, read back |

## Known drift

- `pocketshop/savings-trading` (opened 2026-11-18 in `36cd6e6`, closed 2026-11-20)
  was the fleet's one unreachable loop: declared in no Loops table and naming a
  `skill: savings-markets` that did not exist. Binder closed both halves itself —
  the skill plus `trading_gate.py` and 15 tests, and the Loops and Skills rows —
  so the rule held in the right direction: the owner moved, the index only
  followed.

- `ai-daw/stem-separation`, `anser/faq-distill`, `turbofit/benchmark-rung` and
  `turbofit/peer-discovery` exist on disk but are not yet declared in their own
  Skills tables — only the owning bot edits its BOT.md. Filed as a fleet
  `[BOTS]` item on 2026-11-17, extended 2026-11-21; the validator counts them
  (41 skills, four of them orphans) but no owning bot's published skill list
  reaches them, so the procedure exists and is unreachable from the bot that
  owns it. TurboSouth closed its own share of this on 2026-11-15 by declaring
  `support-verify`, and Binder its share on 2026-11-20 by declaring
  `savings-markets`, which proves the fix is a one-line edit the owner makes, not
  a fleet rewrite; ai-daw and anser owe one line each and TurboSouth owes two.
- **Publish drift, found and fixed 2026-11-24.** Seeding Folio on 2026-11-23
  wrote `bots/resume/` and logged `bot-resume` as published, but no
  `$HERMES_HOME/skills/bots/resume/` existed: the tenth bot was unloadable, and
  `bot-bot-wiki` still said "nine bots" while `bot-hermes` predated its own Needs
  edit. `tools/publish_skills.py` re-rendered all ten loaders plus the two fleet
  skills. The check that catches this class is each loader's mtime against its
  BOT.md — a log line claiming a publish is not evidence of one.
- `ssi`: the program inventory the fleet queue still lists as missing to-do work
  is already written into `bots/ssi/BOT.md` (six programs, first form each,
  2026-11-07). The bot is now explicitly two-layer — public template plus
  `$HERMES_PRIVATE/ssi/profile.md` — so what still blocks specific operation is
  the operator creating that private profile, not missing writing. At 17 days
  blocked the demotion to `paused` is overdue as an owner edit; `bot-archive` now
  carries the exact four lines that edit touches, so the pause and its unpause
  ask cannot drift apart.
- **Private-profile pattern.** Where a bot needs household/account/device facts,
  the repo carries only the shape and the loader contract; the values live at
  `$HERMES_PRIVATE/<bot>/` (defaulting to `~/.hermes/private/<bot>/`) and are
  never committed. `ssi` is the reference implementation
  (`bots/ssi/.system/profiles/README.md`); `pocketshop` applies it to seller
  identity and tokens, `hermes` to device names, `resume` to the client's whole
  history. A bot that hardcodes such a value in a tracked file is drifted,
  whatever its tests say.
- `hermes`: the 443 serve proxy points at `127.0.0.1:8788` (nothing listening),
  not the documented `8091`; day 18 as of 2026-11-27, while the gateway on 8091
  is healthy (`/health` 200, `main: federated`). `:9119` answers on the container
  IP as well as loopback (platform-managed bind). Control-plane map sync has gone
  stale twice (11-13, 11-26→27) with the node listing itself `offline` while peers
  still reach it. Recorded in its own log, unfixed — both need an operator
  decision, not glue.
- `bots/_fleet/skills/*` (`sovthpaw-voice`, `wifi-scanner-control`) **is now**
  installed by `tools/publish_skills.py` under `$HERMES_HOME/skills/fleet/<name>/`
  (2026-11-16), and `verify_bots.py` counts the fleet skills explicitly.
- `.system/` is gitignored, so queues and injections are per-clone state — yet
  both clones have been carrying tracked edits to `bots/_fleet/.system/queue.md`
  since it was force-added, so the queue is now half-tracked: edits to it commit,
  edits to `bots/<slug>/.system/*` do not. Worth either tracking the whole tree
  or none of it; until then the queue lives in the clone that wrote it. This
  bit for real on 2026-11-25: `bots/resume/.system/` in the working clone
  (`~/work/agent-wiki`) held only `profiles/`, while the live clone
  (`~/.hermes/wiki`) held Folio's `queue.md` (three open rows), `continuity.md`
  and `injections.md`. A reconcile run from the working clone therefore counted
  24 open rows, not 27, and reported Folio as idle — the "empty queue is a
  missing clone" trap on exactly one bot. Both clones now carry all four files;
  the durable fix is a start-of-run `cp -a ~/.hermes/wiki/bots/*/.system/` into
  the working clone (or a single clone), not another prose note.
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
- `turbofit` computes the local hardware budget that `ai-daw` and `youtube` want
  for local inference. TurboSouth publishes the matrix; the other two read it.

## Standing rules

- Public output says **sovthpaw**, never the operator, never Southpaw.
- Nothing spends money without a hold point satisfied.
- Every bot's `## Log` is append-only and newest-first.
