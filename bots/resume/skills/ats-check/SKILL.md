---
name: ats-check
description: Audit a resume for ATS parsability and screening quality.
version: 1.0.0
author: Folio
license: MIT
metadata:
  hermes:
    tags: [resume, ats, format, audit]
---

# ATS check

Most résumés are rejected by a parser before a person sees them. The parser is
boring and literal; the audit is too.

## Procedure

1. **Run the linter** and fix every `error`:

   ```bash
   python bots/resume/scripts/resume.py lint drafts/<master>.md   # human-readable
   python bots/resume/scripts/resume.py lint drafts/<master>.md --json  # machine
   ```

   `--strict` exits nonzero on warnings, which is the gate before a render.
2. **Check the things a linter cannot see** by reading the rendered document:
   - one column, no tables, no text boxes, no headers/footers carrying contact
     info (many parsers drop them)
   - standard headings: `Professional Summary`, `Core Skills`, `Experience`,
     `Education` — not `Career Narrative` or `Where I've Been`
   - dates as `YYYY – YYYY` or `Mon YYYY – Mon YYYY`, consistent down the page,
     every role dated
   - contact line with city/state, email, phone; no street address, no photo
   - 11–12 pt body, 10 pt contact, readable margins, no graphic flourishes
   - PDF export only after the docx reads back correctly
3. **Check the filename.** `First-Last-Resume.pdf` — not `resume_final_v3` and
   never a date in the name. The file is what a recruiter sees in a list of
   forty, and a versioned mess reads as unserious.
4. **Check the keyword layer** against one real posting (see `role-tailor`):
   coverage under ~50% on a posting the client wants is a rewrite problem, not a
   formatting problem.
5. **Check the story in 30 seconds.** Read only the top third and the last role's
   first bullet. If that does not say *what this person does and at what scale*,
   the summary is wrong regardless of the lint score.

## Rules

- **A warning that names a missing fact is not a formatting defect.** Keep it as
  a `[[CONFIRM]]` and put it in the client's ask list; do not invent the number to
  clear the gate.
- **Never clear an error by deleting evidence.** Deleting a role to fix date
  order is a different, worse résumé.
- **Never claim ATS compliance from a lint pass alone.** The lint checks text; the
  visual checks are read from the rendered file.
- **Recorded audits go beside the draft** as `drafts/<name>.audit.txt` — the
  exact lint output that the version passed, so a later edit can be diffed
  against it.
