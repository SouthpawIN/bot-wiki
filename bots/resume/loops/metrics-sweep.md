---
type: loop
slug: metrics-sweep
bot: resume
schedule: "0 8 1 * *"
state: spec
skill: evidence-ledger
created: 2026-11-23
---

# metrics-sweep

Monthly, 08:00 on the 1st. A résumé decays quietly: facts go unconfirmed, a
certification expires, a role sits with no number in it for a year.

## Prompt

Read `$HERMES_PRIVATE/resume/ledger.md` (default `~/.hermes/private/resume/ledger.md`)
and the newest draft in `$HERMES_PRIVATE/resume/drafts/`. Report, one line each:

- every bullet still carrying `[[CONFIRM: …]]`, grouped by role, with the exact
  fact asked for;
- any role where no bullet carries a number;
- any certification whose expiry is within 60 days, or that has no expiry
  recorded;
- any draft older than 90 days while `source/` has newer material.

Close with the single highest-value question to ask the client this month. If
there is nothing to report, say "clear" and stop.

## Stop condition

Read-only: it reads the ledger and drafts, writes one injection line, and touches
nothing else. It never edits the résumé, never renders, never sends, and writes
nothing outside the private path. If `ledger.md` does not exist, that is the
finding: intake has not been run for this client.
