---
type: schema
bot: ssi
title: Private profile schema
tags: [ssi, private-profile, schema, template]
---

# Private profile schema — `$HERMES_PRIVATE/ssi/profile.md`

This file documents the **shape** of the runtime profile Beacon loads before
anything else. It contains placeholders only. A real profile is written by the
operator on his own machine at `$HERMES_PRIVATE/ssi/profile.md` (default
`~/.hermes/private/ssi/profile.md`) and is **never committed** — not to this
repo, not to a fork, not to a gist.

Copy the block below into the private path and replace every `<...>` with a real
value. If the file is missing, Beacon runs generically: it explains the
programs, asks for the facts, and writes nothing outside the private path.

## Frontmatter

```yaml
---
schema: hermes.ssi-profile/v1
season: <YYYY-Qn>                 # reporting season this inventory was built for
jurisdiction: <two-letter>        # the state whose rules apply
household: [<beneficiary-id>...]  # stable ids, never names
programs: [<program>...]          # subset of the generic program table
deadlines: []                     # dated rows; empty is valid
updated: <YYYY-MM-DD>
---
```

Required keys: `schema`, `season`, `jurisdiction`, `household`, `programs`,
`deadlines`, `updated`. A profile missing any of them is rejected and Beacon
stays generic rather than guessing the gap.

## Sections

### `## Roles`

Who does what, in role words only:

```markdown
- applicant: the operator
- beneficiary: <beneficiary-id> — <relationship-role>
- authorised representative: <none|the operator>
```

### `## Beneficiaries`

One block per id. Facts come from documents, not memory:

```markdown
### <beneficiary-id>
- age band: <0-5|6-12|13-17|18+>
- programs: [<program>...]
- diagnoses on file: <count> — detail lives in the case dir, not here
- documents in hand: <n>
- documents missing: <n>
```

Age **band**, not a birth date, is enough for eligibility reasoning; the exact
date, if needed for a form, is read from the source document at fill time.

### `## Programs`

Status per beneficiary, one row each:

```markdown
| program | beneficiary | status | next action | due |
|---|---|---|---|---|
| <program> | <beneficiary-id> | <approved|pending|never filed|unknown> | <action> | <YYYY-MM-DD|—> |
```

### `## Case inventory`

```markdown
| case ref | agency | beneficiary | opened | last notice | state |
|---|---|---|---|---|---|
| <case-ref> | <agency> | <beneficiary-id> | <YYYY-MM-DD> | <YYYY-MM-DD> | <open|closed|appeal> |
```

`case ref` is the operator's own local handle for the folder; it does not need to
be the agency's number. The agency number lives in the case dir, sourced from the
notice that carries it.

### `## Deadlines`

```markdown
| due | obligation | beneficiary | source document | done |
|---|---|---|---|---|
| <YYYY-MM-DD> | <obligation> | <beneficiary-id> | <relative path in case dir> | <y|n> |
```

### `## Documents in hand`

```markdown
- <relative path in case dir> — <doctype> — <YYYY-MM-DD received>
```

### `## Portals and contacts`

```markdown
- <agency>: <portal URL> — login stored in <secret store ref>, never here
```

Never put a password, SSN, or full account number in this file. Reference the
secret store entry; the value stays in the store.

### `## Constraints`

Free-form, role-worded notes the bot must respect, e.g. preferred contact method
or a hard "ask before anything with a hearing date".

## Load contract

1. Resolve `$HERMES_PRIVATE`, else `~/.hermes/private`.
2. Read `ssi/profile.md`. Validate the required keys.
3. If valid: every program, deadline, household and case fact comes from it, and
   the case dir beside it. Beacon is specific.
4. If absent or invalid: generic mode. Explain, ask, write nothing to disk
   outside the private path, and never hardcode a household or a state.
5. A run that would need a private value in a public file stops and reports the
   gap instead of writing it.
