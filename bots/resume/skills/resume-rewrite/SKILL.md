---
name: resume-rewrite
description: Rewrite a resume master in reverse-chronological order.
version: 1.0.0
author: Folio
license: MIT
metadata:
  hermes:
    tags: [resume, writing, structure, bullets]
---

# Résumé rewrite

The rewrite is structural before it is stylistic. Order and consolidation fix
more screening failures than any adjective.

## The canonical shape

```markdown
# First Last
City, ST · email · phone

## Professional Summary
Two to three sentences.

## Core Skills
- Grouped keyword lines, one per line.

## Experience

### Title — Employer, City, ST
*YYYY – YYYY*
- Verb + object + measurable result.

## Education
- Only if a credential exists. Omit the heading entirely if not.
```

## Order of work

1. **Diagnose first:** `python bots/resume/scripts/resume.py lint <source>.md`.
   Read every `error`. Do not edit before you have the list.
2. **Fix chronology.** Strict reverse order by end date; a current role goes
   first with `Present`. Overlapping concurrent jobs (gig work alongside a
   part-time job) are listed by end date, and the overlap is noted once in the
   summary or left alone — never reshuffled to hide it.
3. **Consolidate.** Same employer twice = two blocks, titled for the level at
   each point, with the gap between them accounted for. Do not merge a 2005–2010
   role and a 2018–2021 role into "2005–2021": that claims eight unworked years.
4. **Replace the objective.** Delete `Objective` outright. Write
   `Professional Summary`: years of experience, the two or three credentials that
   matter, the scope (covers, team, revenue), and the target role. No "passionate",
   no "excited to join".
5. **Reframe gaps honestly.** A caregiving or career break is a role with real
   work in it: household operations, scheduling, and the administrative support
   actually provided to a business. Never leave the words "stay at home mom" as a
   job title, and never invent a revenue figure to make it sound bigger.
6. **Rewrite every bullet** to `Verb + object + result`, one to two lines, no
   first person, no "responsible for":
   - start with a strong verb (owned, built, trained, cut, promoted, captained,
     negotiated, scheduled, resolved, maintained)
   - name the thing and the scale
   - end on the outcome if the outcome exists
   - one bullet per achievement, not one per duty
   - cut any bullet that only restates the job title
7. **Move periods, not adjectives.** A promotion inside a block is the strongest
   line available: `Promoted hostess → server → head waiter → lead trainer over
   six years.` Prefer it to any self-description.
8. **Skills section = the ATS layer.** 8–10 lines, keyword phrases the employer
   searches (system names, certifications, functions), grouped: leadership, craft
   skills, systems, certifications, physical/technical. Only what is true.
9. **Cut the footer.** "References available upon request" is obsolete and costs a
   line. Same for a full street address — `City, ST` is enough.
10. **Verify:** `resume.py lint drafts/<master>.md` → `0 errors`. Any remaining
    warning is a client fact, so it stays in the ask list from `evidence-ledger`.

## Rules

- **Never add a number the client did not give.** Rewrites make existing facts
  legible; they do not create new ones.
- **Never soften a title.** `Maid` becomes `Commercial Cleaning Technician`
  because that is what the work was; `Server` never becomes `Hospitality
  Manager`.
- **Never pad to two pages.** Hospitality hiring reads one page first. Past ~15
  years, older roles get one line each or move to a single `Earlier experience`
  line.
- **Keep the client's voice.** The document has to survive them being asked about
  it in an interview; plain, concrete phrasing beats polished abstraction.
- **One tense per role.** Present tense for the current job, past for everything
  else.
- **Verify by reading the render back,** not by trusting the converter: open the
  `.docx` and confirm every heading and the last bullet are present.
