---
name: bot-archive
description: Park a bot as paused without deleting it; keep its artifacts loadable.
version: 1.0.0
author: Klerik
license: MIT
metadata:
  hermes:
    tags: [bots, archive, lifecycle]
---

# Bot archive

Archiving is the only way a bot stops. A bot is never deleted and its history is
never rewritten: `status: paused` keeps every line of the log, every skill, every
loop spec and the queue exactly where they are, so a resumed bot resumes instead
of restarting.

## When to archive

| Trigger | Action |
|---|---|
| `status: blocked` for 14+ days with no human reply | demote to `paused` once, and say so in one line — never nag on later runs |
| The project is over: shipped, abandoned, or absorbed into another bot | archive on the owner's word |
| A bot never produced an artifact and has no reachable blocker | archive as a seed that did not take |

Blocked is a claim on the operator's hands; paused is a statement that nobody is
holding it. The demotion is what turns an unanswered ask into an honest status —
which is why it is a one-line edit, not a shutdown.

## What changes

Only the owning bot's `BOT.md`, and only these lines:

1. `status:` in frontmatter → `paused` (keep `created:`; do not bump `owner:`).
2. `archived: YYYY-MM-DD` added directly under `status:` with the one-line reason
   that fired it, e.g. `archived: 2026-11-22 — blocked 15 days, no reply; ask
   still stands in Needs`.
3. One line at the top of `## Log` (newest-first is the log's rule):
   `YYYY-MM-DD — paused: <reason>. Unpause when <the one thing> lands.`
4. `## Needs from the operator` shortened to the single item that would unpause
   it, so a resumed session reads the live ask and not a stale pile.

Nothing else moves. Leaving the section, the Skills table, the Loops table and
the `.system/` files intact is the point: the bot must stay loadable as
`skill: bot-<slug>` while paused, because the reason to unpause it arrives by
someone reading it.

## Then, in the same run

1. `bots/_fleet/FLEET.md`: the row's Status becomes `paused`, the `Blocked on`
   cell keeps the unpause ask. The index follows the bot; the bot is never
   edited to match the index.
2. Loops: any `live` loop gets its cron job disabled before the status flips —
   `state: live` and `paused` in the same file is an index bug. Never arm a new
   one on the way out.
3. Queue: every `[ ]` row targeting the paused bot gets `HOLD: bot paused` on its
   reason line rather than being deleted; a row that would spend money or post
   publicly stays `[ ]` regardless.
4. Injection: one `[UNREAD]` line, outcome-first — "Beacon is paused after 15
   days blocked; unpause needs `$HERMES_PRIVATE/ssi/profile.md`" — so the human
   hears it once.
5. Publish: `python3 tools/publish_skills.py`, so `bot-<slug>` renders the paused
   status rather than the last live one.

## Unpause

Reverse it exactly: `status:` back to the status the bot earns (`seeding` unless
a loop is proven, `live` if it was), drop the `archived:` line, restore the full
Needs section from the log, re-arm only loops the operator approves, log one line
naming what unblocked it. Do not resurrect a discarded artifact — check the
queue's history for a row closed by an owner and take their version.

## Stop conditions

- If the demotion is owed but this run does not own the bot's `BOT.md`, file it
  as one fleet `[BOTS]` row, name it once in the injection, and stop. This skill
  describes the owner's edit; it does not license making it.
- If `status: blocked` but `Needs from the operator` is empty, that is a shaping
  bug: write the ask first (one line, from the bot's own queue), then archive.
