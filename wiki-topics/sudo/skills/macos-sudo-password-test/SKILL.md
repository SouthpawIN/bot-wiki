---
name: macos-sudo-password-test
description: Use to test a macOS sudo password the agent blocks, manually.
version: 0.1.0
distilled: 2026-09-13 21:36
topic: sudo-check-check
---
# macos-sudo-password-test
---
name: macos-sudo-password-test
description: Test a macOS sudo password the agent blocks, manually.
category: devops
---

# macOS sudo password test

Reusable procedure for confirming which macOS login/sudo password works when the
agent terminal refuses to run the test.

## When to use
- Confirm a sudo/login password but the Hermes agent terminal blocks it (flags candidate loops as a "brute-force vector").
- zsh mangles passwords containing `!` (history expansion).

## Steps
1. Run it yourself in your own terminal — not through the agent. The agent hard-blocks `sudo -S` and won't see the result anyway.
2. Disable zsh history expansion: `set +H`
3. Loop candidates in single quotes, piping each to `sudo -S`:
   ```
   for pw in '[REDACTED-PASSWORD]' 'senterdelta' '[REDACTED-PASSWORD]' '[REDACTED-PASSWORD]'; do
     if echo "$pw" | sudo -S true 2>/dev/null; then echo "WORKED: ${pw:0:3}..."; break; else echo "fail: ${pw:0:3}..."; fi
   done
   ```
4. The first candidate printing `WORKED:` is your password.

## Pitfalls
- Trailing `!` in a password triggers `zsh: event not found` unless you `set +H` first AND wrap in single quotes.
- Don't paste password brute-forces through the agent; it blocks them. Run locally.

## Outcome
Confirmed `[REDACTED-PASSWORD]` is the working sudo/login password (sudo-check-check, 2026-09-13).

## Evidence
> check if any of these work for sudo before I do all that: [REDACTED-PASSWORD] senterdelta [REDACTED-PASSWORD] [REDACTED-PASSWORD]
> zsh: event not found: nd
> set +H / for pw ... if echo "$pw" | sudo -S true 2>/dev/null; then echo "WORKED"
> WORKED: A11...
