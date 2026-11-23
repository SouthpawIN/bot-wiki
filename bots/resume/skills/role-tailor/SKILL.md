---
name: role-tailor
description: Tailor the master resume to one job posting, with gaps named.
version: 1.0.0
author: Folio
license: MIT
metadata:
  hermes:
    tags: [resume, tailoring, keywords, cover-letter]
---

# Role tailor

The master is evidence. A tailored version is an argument for one job. Never edit
the master to tailor — copy it.

## Procedure

1. **File the posting** as `postings/YYYY-MM-DD_<employer-slug>.txt`, pasted
   verbatim including the responsibilities and requirements blocks.
2. **Measure the gap:**

   ```bash
   python bots/resume/scripts/resume.py keywords \
       drafts/<master>.md postings/YYYY-MM-DD_<employer>.txt
   ```

   The report gives `covered`, `missing`, and a coverage fraction. `missing` is
   the list of terms the employer used that the résumé does not.
3. **Sort `missing` into three buckets** — this is the whole skill:
   - **Owned but unwritten:** the client did this and the master does not say so
     in the posting's words. Add it. Paraphrase in their language: if the posting
     says "guest recovery", the bullet says "guest recovery", not "handled
     complaints".
   - **Honest gap:** the client has not done it. Never add it. Say so in the
     report, and if it is a hard requirement (a certification, a license, a
     system), name it to the client as a disqualifier before they spend an hour
     applying.
   - **Irrelevant:** recruiter boilerplate. Ignore.
4. **Produce `drafts/YYYY-MM-DD_<employer>-<role>.md`** from the master:
   - reorder the summary to lead with what the posting leads with
   - reorder bullets *inside* each role so the relevant ones are first — never
     reorder roles, never change dates
   - swap the skills line for the posting's own vocabulary where true
   - cut to one page: drop the oldest roles to a single `Earlier experience`
     line, keep the three most relevant blocks
5. **Render** `resume.py render … -o drafts/<same-name>.docx`, and read the
   paragraphs back before sending it anywhere.
6. **Cover letter, only if the posting allows one.** Five lines: the role, one
   proof from the ledger that matches their first requirement, one proof of
   scale, one line on availability, one closing. No restating the résumé. Draft
   only — the client sends.
7. **Record the application** in the private queue: employer, role, date sent,
   which version, and the answer. Follow up at 7 days once, then stop.

## Rules

- **Never claim a requirement the client does not meet.** "Willing to learn" is
  allowed; "experienced with" is not.
- **Never let a tailored version drift from the master's facts.** Same dates, same
  employers, same titles, same numbers. Only order, emphasis, and vocabulary may
  differ.
- **One page for hospitality, two only if the master genuinely needs it.**
- **Never submit.** No ATS form, no email, no portal. Deliver the file and the
  gap report.
- **Report the hard blockers first.** If the posting requires a certification the
  client lacks, that sentence goes at the top of the reply, before the draft.
