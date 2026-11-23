# Resume bot — private profile schema

The public bot carries the method; the private profile carries the client.
Nothing in this directory is committed — `bots/<slug>/.system/` is gitignored,
and the real profile lives outside the repo entirely.

## Path

- `$HERMES_PRIVATE/resume/profile.md`
- default: `~/.hermes/private/resume/profile.md`

Loaded first on every run, before any skill or draft is touched.

## Profile shape (placeholders only)

```markdown
# Client profile — resume

## Client
- Display name: <first last>
- Preferred name: <short name>
- Relationship: <client | self | family>
- Location: <City, ST ZIP>          # header renders City, ST only
- Contact: see contact.md beside this file
- Availability: <fact or [[CONFIRM]]>

## Target roles (priority order)
1. <role family> — <market>
2. <role family> — <market>

## Positioning
- <career arc in two lines>
- <strongest differentiators>
- <honest gaps>

## Constraints
- Unmeasured facts stay [[CONFIRM]]; never invent numbers.
- Never submit, send, or post.
- Never publish these contents to the public wiki.

## Files
- source/ — the résumé as supplied, dated
- ledger.md — generated evidence ledger
- drafts/ — master .md, rendered .docx, tailored copies
- postings/ — one posting per file
```

## Absent profile

Generic mode: explain the method, ask for the source résumé and one target role,
and write nothing outside the private path. Never assume a career, a market, or a
certification.
