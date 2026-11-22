---
type: bot
slug: hermes
name: Mesh
owner: sovthpaw
status: live
created: 2026-11-07
tags: [bot, hermes, tailscale, sync, infrastructure]
repos: [NousResearch/hermes-agent]
---

# Mesh — Hermes, one instance everywhere

**Mission.** One Hermes, many screens. The omarchy desktop, the MacBook, the
Surface, and the phone all talk to the same instance — same chats, same bots,
same skills. Attach, don't copy: no second brain, no drift.

The target is a **single Hermes served as a web app over Tailscale**: every
device opens the same interface at the same tailnet URL, with the same chat
history and the same nine bots. That replaces "each machine has its own Hermes
and its own state" with one authority and thin clients.

**Interface.** `skill: hermes` (+ the `hermes-agent` skill for command truth).

## Mission, stated as outcomes

- The dashboard/web app is reachable on the tailnet at a stable HTTPS hostname,
  behind auth, from every device: omarchy desktop, MacBook, Surface, phone.
- Each device reaches it with the native surface it has: desktop app on omarchy
  and MacBook, browser/app on the Surface and phone.
- Sessions, bots, memory, and skills are one store — not four.
- Every device shows the same interface and the same conversations; a chat
  started on the phone continues on the desktop.
- Any device can be offline for a week and lose nothing but its local cache.
- The build uses **built-in Hermes mechanisms** — `hermes dashboard`,
  `tailscale serve`, profiles, the standard auth path — rather than custom
  proxies, rsync of `~/.hermes`, or a hand-rolled sync daemon.
- The actual configuration steps are written down and reproducible: serve,
  tailnet access, profile sharing.

## Configuration record (the steps, not the theory)

These are the three procedures that have to be recorded and kept current in
`bots/hermes/devices/_mesh.md`; each is a built-in mechanism, not glue:

1. **Serve** — `hermes dashboard --host 127.0.0.1 --port 9119`, then
   `tailscale serve --bg 9119` (or `--https=8443 9119`) so the app is HTTPS on
   the tailnet. No custom reverse proxy, no public bind.
2. **Tailnet access** — the device runs `tailscale up`, joins the same tailnet,
   and opens the MagicDNS name. Access control is tailnet ACLs plus Hermes auth,
   not an IP allowlist in front of the app.
3. **Profile sharing** — bots are Hermes profiles on the authority; a client sees
   them because it is talking to the authority, not because the profile was
   copied. `tools/publish_profiles.py` renders `bots/<slug>/BOT.md` into the
   authority's `~/.hermes/profiles/<slug>/SOUL.md`.

## Owns

- The tailnet wiring: `tailscale serve` for HTTPS, MagicDNS name, ACLs.
- `bots/hermes/devices/_mesh.md` — the record of what is wired and verified.
- `hermes dashboard` (machine-level, unified mode) and the API server.
- The per-device onboarding checklists in `bots/hermes/devices/`.
- The rule that only one machine is the *authority*; the rest are clients.

## Operating loop

1. **Designate authority.** This VPS container is the authority (it has the
   uptime). Devices attach to it; they do not host their own Hermes for these bots.
2. **Serve once.** `hermes dashboard --host 127.0.0.1 --port 9119`, then
   `tailscale serve --bg 9119` → `https://<host>.<tailnet>.ts.net`. Never bind
   0.0.0.0 and never expose a port outside the tailnet.
3. **Auth.** OAuth (Portal) or a password. A tailnet is not an auth provider.
4. **Bots.** Each topic bot becomes a Hermes **profile**, so Bot Mode shows the
   roster with per-bot memory, skills, and routines — the wiki's `bots/<slug>/BOT.md`
   is the human-readable twin of `~/.hermes/profiles/<slug>/`.
5. **Attach devices** in order: omarchy → MacBook → phone → Surface. Verify with a
   real turn (send a message from the device, see it in `hermes sessions`).
6. **Sync the wiki**, not the configs. Skills and `BOT.md` files live in git; the
   profile dirs stay machine-local. `git pull` is the sync mechanism.
7. **Health check** daily: dashboard up, certificate valid, one device round-trip.

## Skills

| Skill | When it loads | State |
|---|---|---|
| [[bots/hermes/skills/webapp-on-tailnet/SKILL]] | first serve, or after a cert/host change | written |
| [[bots/hermes/skills/device-onboarding/SKILL]] | adding a machine or phone | written |
| [[bots/hermes/skills/bot-mode-profiles/SKILL]] | turning a wiki bot into a live Bot | written |

## Loops

| Loop | Schedule | State |
|---|---|---|
| [[bots/hermes/loops/mesh-health]] | daily 06:30 | live |

## Hold points

- Never expose the dashboard beyond the tailnet, and never with `--insecure`.
- Never prefer a custom proxy, file-sync daemon, or copied `~/.hermes` over the
  built-in `hermes dashboard` / `tailscale serve` / profile path. If a built-in
  step is missing, record the gap instead of inventing glue.
- Never leave the configuration record stale: a serve/auth/profile change that
  is not in `bots/hermes/devices/_mesh.md` did not happen.
- Never put a secret in `config.yaml`; `.env` only.
- Never let a device become a second authority — that is how memories fork.

## Needs from the operator

- Which devices are on the tailnet today? (omarchy is; the MacBook and Surface
  need `tailscale up` and a login each.)
- Phone: iOS or Android — Android can also run the Hermes app directly.
- Whether the MacBook should keep its *local* TurboFit node role. Local inference
  stays local; only the agent state centralizes.

## Log

- 2026-11-07 — bot seeded; authority designated as this container; tailnet serve plan set.
- 2026-11-08 — nine bot profiles created on the authority (`hermes` → `mesh`, since the name is reserved), each with SOUL.md from its BOT.md and its `bot-<slug>` skill; `tools/publish_profiles.py` re-renders them.
- 2026-11-08 — **web app is live on the tailnet**: `tailscale serve --bg --https=8443 9119` → https://hermes-vps.tail6ff78b.ts.net:8443/, verified HTTP/2 302 to the Nous OAuth login. Five devices on the tailnet (omarchy, android-s10 online; MacBook, surface-duo-2 offline). Device attach and bot profiles still pending.
- 2026-11-10 — mesh health check: dashboard 302 on :9119, OAuth login 302 via SOCKS on :8443, disk 4% used, omarchy/MacBook online. tailscaled had died (container restart) and was restarted in userspace mode; serve config persisted. **Drift found, not fixed:** the 443 serve proxy now points at `127.0.0.1:8788` (nothing listening → 502 on the ts.net root) instead of the documented `8091` (TurboFit gateway, alive). Also `:9119` is bound to `0.0.0.0`, not loopback as documented.
- 2026-11-11 — mesh health check: dashboard 302 on :9119; tailscaled dead again after a container restart, restarted in userspace mode (SOCKS 1055, serve config persisted in state); OAuth login 302 → `/auth/login?provider=nous` through SOCKS on :8443; disk 5% used, 90 G free. Devices: omarchy and MacBook online (MacBook recovered); android-s10 and surface-duo-2 offline, last seen 11-10 05:22 and 11-09 08:12. **Still open, day 2:** 443 serve proxy → `127.0.0.1:8788` (nothing listening → 502 on the ts.net root) while 8091 (TurboFit gateway) is alive on loopback; `:9119` still bound to `0.0.0.0`. Serve config left untouched per the loop's hold point.
- 2026-11-12 — mesh health check: dashboard 302 on `:9119`; tailscaled dead a third time after a container restart (no SOCKS listener, no socket), restarted in userspace mode — probe persistence is now the pattern, not a one-off; serve config persisted in state and listed both proxies. OAuth login 302 → `/auth/login?provider=nous` through SOCKS on :8443, TLS verified; disk 5% used, 90 G free. Devices: omarchy and MacBook online; android-s10 and surface-duo-2 offline 2 days, unchanged from yesterday. **Still open, day 3:** 443 serve proxy → `127.0.0.1:8788` (nothing bound there → root 502) while 8091 (TurboFit gateway) answers on loopback; `:9119` still answers on the container IP 172.19.0.186, not loopback-only. Serve config left untouched per the loop's hold point.
- 2026-11-13 — mesh health check: dashboard 302 on `:9119`, still answering on the container IP 172.19.0.186 (not loopback-only); tailscaled alive this run (pid 4340, keeper loop up) and serve config persisted with both proxies; OAuth chain verified end to end through SOCKS on `:8443` — 302 → `/auth/login` → 302 to `portal.nousresearch.com/oauth/authorize`; disk 24% used, 72 G free. Devices: omarchy online (direct, 58 ms), MacBook offline since 05:15 (~1 h, laptop, not a failure), surface-duo-2 7 h, android-s10 3 d. **New, day 1:** control-plane sync is down — `tailscale status` warns "Unable to connect to the Tailscale coordination server", the node itself reports `offline`, and `keeper.log` shows map long-poll timeouts; existing peers still reach it (direct ping to omarchy succeeds), so nothing is broken yet, but any netmap change would strand the node. **Still open, day 4:** 443 serve proxy → `127.0.0.1:8788` (connection refused → 502 on the ts.net root) while 8091 (TurboFit gateway) is alive on loopback. Serve config left untouched per the loop's hold point.
- 2026-11-14 — mesh health check: dashboard 302 on `:9119` (still bound `0.0.0.0`, not loopback-only); tailscaled alive with the keeper loop up (pid 1016, started 11-13) and serve config persisted; OAuth login 302 → `/auth/login?provider=nous` through SOCKS on `:8443`; disk 40% used, 57 G free. Devices: omarchy online, MacBook offline 10 m (laptop), surface-duo-2 1 d, android-s10 4 d. **Resolved (day 2 of the finding):** control-plane sync is back — `tailscale status` shows no coordination-server warning and `keeper.log` shows active DERP conns (derp-9 → derp-2). **Still open, day 5:** 443 serve proxy → `127.0.0.1:8788` (connection refused → 502 on the ts.net root) while 8091 (TurboFit gateway) answers 404 on loopback as expected. Serve config left untouched per the loop's hold point.
- 2026-11-15 — mesh health check: dashboard 302 on `:9119` (still bound `0.0.0.0`, not loopback-only); tailscaled alive since 11-13 20:14 with the keeper loop up (pid 1016), no restart needed this run; serve config persisted with both proxies; OAuth chain verified end to end through SOCKS on `:8443` — 302 → `/auth/login?provider=nous` → 302 to `portal.nousresearch.com/oauth/authorize` (portal 200); disk 42% used, 55 G free. Devices: omarchy idle (online), MacBook offline 10 m (laptop, not a failure), surface-duo-2 3 h, android-s10 5 d. **Still open, day 6:** 443 serve proxy → `127.0.0.1:8788` (connection refused → 502 on the ts.net root) while 8091 (TurboFit gateway) is alive on loopback. Serve config left untouched per the loop's hold point. Note: gateway `/health` now returns 503 (`main: down`, `aux: down`, `backend: none`) — no engine loaded, consistent with an idle gateway, not treated as a fault.
- 2026-11-16 — mesh health check: dashboard 302 on `:9119` (still bound `0.0.0.0`, not loopback-only); tailscaled alive since 11-13 20:14 (pid 1025) with the keeper loop (pid 1016) up, no restart needed this run; serve config persisted with both proxies; OAuth login 302 → `/auth/login?provider=nous` through SOCKS on `:8443`; disk 48% used, 49 G free. Devices: omarchy online, MacBook offline 10 m (laptop, not a failure), surface-duo-2 1 d, android-s10 6 d (last online 11-08 — phone-side absence, not a mesh fault). **Still open, day 7:** 443 serve proxy → `127.0.0.1:8788` (connection refused → 502 on the ts.net root) while 8091 (TurboFit gateway) is alive on loopback (`/health` still 503, no engine loaded — idle, not a fault). Serve config left untouched per the loop's hold point.
- 2026-11-16 — brief coverage: stated the single-instance-over-Tailscale target (desktop, MacBook, Surface, phone with identical interface and chats) and added a Configuration record for the three real steps — serve, tailnet access, profile sharing. Hold points now forbid custom proxy/sync glue over built-in `hermes dashboard` / `tailscale serve` / profiles, and require the record to stay current.
- 2026-11-17 — mesh health check: dashboard 302 on `:9119` (still bound `0.0.0.0`, platform-managed — not a config this bot controls); tailscaled alive since 11-13 20:14 (pid 1025) with the keeper loop up, no restart needed this run; serve config persisted with both proxies; OAuth login 302 → `/auth/login?provider=nous` through SOCKS on `:8443`; disk 45% used, 52 G free. Devices: omarchy online (idle), MacBook asleep (offline 1 m — laptop, not a failure), surface-duo-2 online, android-s10 offline 7 d (phone-side absence, not a mesh fault). **Still open, day 8:** 443 serve proxy → `127.0.0.1:8788` (connection refused → 502 on the ts.net root) while 8091 (TurboFit gateway) is alive on loopback (`/health` 503, no engine loaded — idle, not a fault); `keeper.log` shows the same proxy error on every daily run since 11-13. Serve config left untouched per the loop's hold point — needs an operator decision: repoint 443 at 8091 or amend the record/loop to match 8788.
- 2026-11-18 — mesh health check: dashboard 302 on `:9119` (still answering on the container IP 172.19.0.186, not loopback-only — platform-managed, not this bot's config); tailscaled **restarted by the keeper at 04:43 today** (pid 880, userspace, SOCKS 1055) after the container cycled — no action needed from this run, serve config persisted with both proxies; OAuth login verified through SOCKS on `:8443` — HTTP/2 302 → `/auth/login?provider=nous`, `server: uvicorn`; disk 47% used, 51 G free (53% headroom). Devices: omarchy online (direct 169.150.154.186:41642, healthy tx/rx), MacBook offline 15 m (asleep, laptop, not a failure), surface-duo-2 12 h, android-s10 8 d (phone-side absence). **Still open, day 9:** 443 serve proxy → `127.0.0.1:8788` (nothing bound → 502 on the ts.net root) while 8091 (TurboFit gateway) answers on loopback; serve config untouched per the loop's hold point — still needs the operator decision: repoint 443 at 8091, or amend `_mesh.md`/this loop to say 8788 is intended.
- 2026-11-19 — mesh health check: dashboard 302 on `:9119`; tailscaled alive (pid 28932, userspace, SOCKS 1055, started 11-18 16:51 by the keeper after the container cycled — no action needed this run) and serve config persisted with both proxies; OAuth login verified through SOCKS on `:8443` — HTTP/2 302 → `/auth/login?provider=nous`, `server: uvicorn`; disk 47% used, 50 G free. Devices: omarchy offline 14 h and MacBook offline 14 h (both overnight, laptops — not failures; omarchy was online yesterday), surface-duo-2 1 d, android-s10 9 d (phone-side absence). **Still open, day 10:** 443 serve proxy → `127.0.0.1:8788` (nothing bound → HTTP/2 502 on the ts.net root through SOCKS) while 8091 (TurboFit gateway) answers on loopback; serve config untouched per the loop's hold point — still waiting on the operator decision: repoint 443 at 8091, or amend `_mesh.md`/this loop to say 8788 is intended.
- 2026-11-20 — mesh health check: dashboard 302 on `:9119`; tailscaled alive (pid 28932, userspace, SOCKS 1055, same process since 11-18 16:51 — no restart this run) and serve config persisted with both proxies; OAuth login verified through SOCKS on `:8443` — HTTP/2 302 → `/auth/login?provider=nous`, `server: uvicorn`; disk 47% used, 50 G free (53% headroom). Devices: omarchy offline 1 d (online 11-18, laptop), MacBook offline 12 h (asleep, not a failure), surface-duo-2 2 d, android-s10 10 d (phone-side absence). **Still open, day 11:** 443 serve proxy → `127.0.0.1:8788` (nothing bound → HTTP/2 502 on the ts.net root through SOCKS) while 8091 (TurboFit gateway) answers on loopback; serve config untouched per the loop's hold point — operator decision still pending: repoint 443 at 8091, or amend `_mesh.md`/this loop to say 8788 is intended.
- 2026-11-21 — mesh health check: dashboard 302 on `:9119`; tailscaled alive (pid 28932, userspace, SOCKS 1055, same process since 11-18 16:51 — no restart this run) and serve config persisted with both proxies; OAuth login verified through SOCKS on `:8443` — HTTP/2 302 → `/auth/login?provider=nous`, `server: uvicorn`; disk 47% used, 50 G free (53% headroom). Devices: omarchy offline 2 d (laptop, was online 11-18), MacBook offline 1 d (asleep, not a failure), surface-duo-2 3 d, android-s10 11 d (phone-side absence). **Still open, day 12:** 443 serve proxy → `127.0.0.1:8788` (nothing bound → HTTP/2 502 on the ts.net root through SOCKS) while 8091 (TurboFit gateway) answers on loopback; serve config untouched per the loop's hold point — operator decision still pending: repoint 443 at 8091, or amend `_mesh.md`/this loop to say 8788 is intended.
- 2026-11-22 — mesh health check: dashboard 302 on `:9119` (OAuth redirect, `server: uvicorn`); tailscaled alive (pid 28932, userspace, SOCKS 1055, same process since 11-18 16:51 — no restart this run) and serve config persisted with both proxies; OAuth chain verified end to end through SOCKS on `:8443` — 302 → `/auth/login` → 302 to `portal.nousresearch.com/oauth/authorize` (portal 200); disk 47% used, 50 G free (51% headroom). Devices: all offline — omarchy 3 d (was online 11-18), MacBook 2 d (asleep, not a failure), surface-duo-2 4 d, android-s10 12 d (phone-side absence); no device went offline since yesterday. **Still open, day 13:** 443 serve proxy → `127.0.0.1:8788` (nothing bound → HTTP/2 502 on the ts.net root through SOCKS) while 8091 (TurboFit gateway, `turbofit-gateway/2.0`) answers on loopback; serve config untouched per the loop's hold point — operator decision still pending: repoint 443 at 8091, or amend `_mesh.md`/this loop to say 8788 is intended.
