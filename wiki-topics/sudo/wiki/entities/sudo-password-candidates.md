---
title: macOS sudo password candidates
created: 2026-09-13
updated: 2026-09-13
type: entity
tags: [tool, person, decision]
sources: [raw/inbox/2026-09-13.md]
confidence: high
---

# macOS sudo password candidates

the operator forgot his Mac's login/sudo password and, before falling back to the full
Recovery Mode dance (Shut Down -> hold power button -> startup options), listed
four candidates to test for sudo ^[raw/inbox/2026-09-13.md]:

> [REDACTED-PASSWORD] / senterdelta / [REDACTED-PASSWORD] / [REDACTED-PASSWORD]

He confirmed **[REDACTED-PASSWORD]** is his working sudo/login password ^[raw/inbox/2026-09-13.md].

## Candidates

| Candidate        | Result        |
| ---------------- | ------------- |
| [REDACTED-PASSWORD]    | **works**     |
| senterdelta      | not confirmed |
| [REDACTED-PASSWORD]      | not confirmed |
| [REDACTED-PASSWORD]       | not confirmed |

The working password feeds a follow-up decision about enabling sudo for the
agent and a pending Tailscale reinstall ([[wiki-topics/sudo-check-check/wiki/decisions/tailscale-reinstall.md|Tailscale reinstall]]) ^[raw/inbox/2026-09-13.md].

## Notes
- Recovering the password sidesteps the Recovery Mode procedure the operator was preparing to do ^[raw/inbox/2026-09-13.md].
- The recovery itself is documented in [[wiki-topics/sudo-check-check/wiki/concepts/macos-sudo-recovery.md|macOS sudo recovery workflow]].
