---
name: evidence-ledger
description: Turn a supplied resume into a traceable evidence ledger.
version: 1.0.0
author: Folio
license: MIT
metadata:
  hermes:
    tags: [resume, intake, ledger, evidence]
---

# Evidence ledger

A résumé is a set of claims. The ledger is where each claim is either sourced or
flagged. Nothing reaches a draft until it exists here.

## Procedure

1. **File the source, unedited.** Copy the photograph, PDF, or docx into
   `$HERMES_PRIVATE/resume/source/` named `YYYY-MM-DD_<what-it-is>.<ext>`. Keep
   the date received. Never edit the original.
2. **Transcribe verbatim** into `source/raw-resume.md` in the canonical shape
   (`# Name`, contact line, `## Section`, `### Title — Employer, City, ST`,
   `*YYYY – YYYY*`, `- bullet`). Keep the client's own wording, including the
   awkward lines. This file is the audit trail, not the draft; it is what you
   re-read when a claim is questioned.
3. **Generate the ledger:**

   ```bash
   python bots/resume/scripts/resume.py ledger \
       $HERMES_PRIVATE/resume/source/raw-resume.md -o $HERMES_PRIVATE/resume/ledger.md
   ```

   Every bullet without a digit gets `[[CONFIRM: metric]]`. Every role with no
   date line gets `[[CONFIRM: dates]]`; every role with no employer gets
   `[[CONFIRM: employer]]`.
4. **Resolve what the page already answers.** Dates, titles, employers and
   locations are usually on the page even when the layout hides them. Read the
   second page before asking about the first.
5. **Write the ask list.** One numbered message, grouped by role, of only the
   facts that change a sentence: covers per shift, team size trained, guests per
   banquet, star rating and trip count, revenue the business ran, month/year of
   each promotion. Cap it at what the client can answer in five minutes.
6. **Re-generate** after every answer and re-check that the ledger and the draft
   agree. A ledger that drifts from the draft is worse than no ledger: it looks
   audited.

## Rules

- **Never fill a marker from plausibility.** "Probably 4.9 stars" is an invented
  rating. Leave `[[CONFIRM]]` and ask.
- **Never merge two employers into one to look tidy.** Two blocks for one
  employer are honest if the person left and returned; the ledger says so in the
  dates column.
- **Never drop a bullet because it is unquantified.** Mark it; the rewrite step
  decides whether to cut it.
- **Never store the ledger outside the private path.** It is a page of the
  client's work history.
- Everything exceptional — overlapping dates, an employer with no location, a
  title that changed mid-block — goes in a `## Open questions` section at the
  bottom of the ledger rather than being silently normalised.
