# Fleet Queue

Cross-bot follow-ups filed while covering each project brief in its own bot
(2026-11-16). `[ ]` proposed, `[~]` reviewing, `[x]` done, `[-]` rejected.
Only the owning bot edits its own `BOT.md`; everything here is a pointer plus a
one-line ask.

## Bot

- [ ] `ssi:private-profile` — the operator creates `$HERMES_PRIVATE/ssi/profile.md` from the published schema; until it exists Beacon stays generic and specific operation stays blocked | sources: bots/ssi/BOT.md, bots/ssi/.system/profiles/README.md
- [ ] `youtube:long-session-parts` — prove a 3-hour OBS recording segments and renders in parts at 1080p60, dead air dropped at pause boundaries | sources: bots/youtube/BOT.md
- [ ] `turbofit:index-pension` — purge retired deep-swe/agentic-pair rows and make every unmeasured configuration read "no measurements yet", suites N/4 | sources: bots/turbofit/BOT.md
- [ ] `turbofit:peer-discovery` — a second TurboFit machine's models must appear as health-checked peer routes without re-download | sources: bots/turbofit/BOT.md
- [ ] `kart-racer:character-audit` — audit every roster entry against the canonical NRCU sheet: at work, no invented accessories, no restyle | sources: bots/kart-racer/BOT.md
- [ ] `ai-daw:second-engine` — add one non-ACE-Step local adapter behind the same Hermes plugin contract and prove a render | sources: bots/ai-daw/BOT.md
- [ ] `hermes:surface-attach` — attach the Surface and phone to the tailnet web app and record serve/tailnet/profile steps in `devices/_mesh.md` | sources: bots/hermes/BOT.md
- [ ] `pocketshop:amazon-path` — decide whether Amazon gets real drafts or CSV export, and record the platform choice per card class | sources: bots/pocketshop/BOT.md

## Skill

- [ ] `publish-fleet-skills` — `tools/publish_skills.py` still renders `bots/*/BOT.md` only, so `bots/_fleet/skills/*` is never installed | sources: bots/_fleet/FLEET.md

## Loop

- [ ] `ssi:deadline-watch-arm` — arm the daily 07:00 deadline watch once the private profile exists; it is read-only and must stay read-only | sources: bots/ssi/loops/deadline-watch.md

## Context

- [ ] `privacy:git-grep-gate` — run the household-fact grep in the nightly reconcile before any commit, not after | sources: bots/ssi/BOT.md, bots/bot-wiki/BOT.md
