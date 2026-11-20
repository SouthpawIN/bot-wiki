# Fleet Queue

Cross-bot follow-ups filed while covering each project brief in its own bot
(2026-11-16). `[ ]` proposed, `[~]` reviewing, `[x]` done, `[-]` rejected.
Only the owning bot edits its own `BOT.md`; everything here is a pointer plus a
one-line ask.

## Bot

- [ ] `ssi:private-profile` — the operator creates `$HERMES_PRIVATE/ssi/profile.md` from the published schema; until it exists Beacon stays generic and specific operation stays blocked | sources: bots/ssi/BOT.md, bots/ssi/.system/profiles/README.md
- [~] `youtube:long-session-parts` — DEFERRED by the operator 2026-11-16: "we deposit YouTube stuff for now cuz I'm not doing anything interesting that needs to be cut but I do want that pipeline ready". Pipeline is built and verified (cutroom CLI + topic grouping + render path; the 4 ffmpeg render tests are marked `slow`, run with `pytest --runslow`). No source material, so no end-to-end run. Reopen when a raw OBS session exists. | sources: bots/youtube/BOT.md, conftest.py
- [x] `turbofit:index-pension` — purge retired deep-swe/agentic-pair rows and make every unmeasured configuration read "no measurements yet", suites N/4 | sources: bots/turbofit/BOT.md | done: turbofit@78f63db — HERMES_INDEX_SUITES is the four Hermes suites, REQUIRED_BENCHMARKS aliases it, records 0, README reads "no measurements yet" and names the old 46.9 record as superseded
- [ ] `turbofit:peer-discovery` — a second TurboFit machine's models must appear as health-checked peer routes without re-download | sources: bots/turbofit/BOT.md
- [x] `kart-racer:character-audit` — audit every roster entry against the canonical NRCU sheet: at work, no invented accessories, no restyle | sources: bots/kart-racer/BOT.md | done: bots/kart-racer/.system/roster.md @ 776d8af, re-verified 2026-11-18 — 35 of 35 canonical entries, each carrying all eight fields (`source`, `species`, `body`, `palette`, `prop`, `voice`, `do not`, `kart`), 71 `[[UNSOURCED]]` markers instead of invented props or vehicles (11 with no sourced kart concept), 6 gap classes + 12 needs-decision items; `roster.json` still 35 characters and the 9 roster tests pass
- [x] `pocketshop:declare-savings-trading` — closed 2026-11-20 by Binder, not by Klerik: `a3cde0cd` wrote `bots/pocketshop/skills/savings-markets/SKILL.md` (93 lines, gate → sourced sentiment → proposal, never an order) plus `trading_gate.py` and 15 tests, and `45723f56` corrected both tables — the Loops row now reads `daily 09:15 | ready` and the Skills row `daily, after the ledger is current | written`, so 13 loops are declared and 13 exist on disk with no orphan. Klerik's parallel skill was discarded during the rebase in favour of the owner's, because the owner's is the one backed by tested code | sources: bots/pocketshop/loops/savings-trading.md, bots/pocketshop/BOT.md § Loops
- [ ] `kart-racer:needs-decision` — Apex's `## Needs from the operator` names only repo visibility, Unity version and a controller, but its audit's riskiest holds are rights, not tooling: Turbo Fit / Sovthpaw's hair and instrument (his own likeness — a hold point), `ee.dd`'s avatar with no reuse license, and six sheets marked "no reuse license is stated"; fold those into the bot's own Needs section so a fresh agent cannot ship a credits screen that claims an unlicensed character | sources: bots/kart-racer/.system/roster.md § Needs decision, bots/kart-racer/BOT.md
- [ ] `ai-daw:second-engine` — add one non-ACE-Step local adapter behind the same Hermes plugin contract and prove a render | sources: bots/ai-daw/BOT.md
- [ ] `hermes:surface-attach` — attach the Surface and phone to the tailnet web app and record serve/tailnet/profile steps in `devices/_mesh.md` | sources: bots/hermes/BOT.md
- [ ] `pocketshop:amazon-path` — decide whether Amazon gets real drafts or CSV export, and record the platform choice per card class | sources: bots/pocketshop/BOT.md
- [ ] `skills-declare-orphans` — `ai-daw/stem-separation`, `anser/faq-distill` and `turbofit/benchmark-rung` exist on disk and pass the validator but none is named in its own BOT.md Skills table, so the owning bot's published skill list cannot reach it; one line each, owners only | sources: bots/_fleet/FLEET.md, bots/ai-daw/BOT.md, bots/anser/BOT.md, bots/turbofit/BOT.md

## Skill

- [x] `publish-fleet-skills` — `tools/publish_skills.py` still renders `bots/*/BOT.md` only, so `bots/_fleet/skills/*` is never installed | sources: bots/_fleet/FLEET.md

## Loop

- [ ] `ssi:deadline-watch-arm` — arm the daily 07:00 deadline watch once the private profile exists; it is read-only and must stay read-only | sources: bots/ssi/loops/deadline-watch.md

## Context

- [x] `privacy:git-grep-gate` — run the household-fact grep in the nightly reconcile before any commit, not after | sources: bots/ssi/BOT.md, bots/bot-wiki/BOT.md
