---
type: bot
slug: ai-daw
name: Riff
owner: sovthpaw
status: seeding
created: 2026-11-07
tags: [bot, music, daw, hermes-plugin, audio]
repos: [SouthpawIN/ACE-Step-DAW]
---

# Riff — AI DAW

**Mission.** A Hermes plugin that drives a DAW from conversation: generate
layers, arrange them, render stems and a mix, without leaving the agent. It is
built on [SouthpawIN/ACE-Step-DAW](https://github.com/SouthpawIN/ACE-Step-DAW),
but ACE-Step is dated — it is the baseline engine, not the ceiling. The plugin's
value is a model-agnostic adapter layer so a better music model is a new adapter,
not a rewrite, and the whole thing stays a **first-class Hermes plugin**: the
contract Hermes expects (manifest, tool naming, permissions, no hidden state)
is not negotiable for any engine behind it.

**Interface.** `skill: ai-daw` — plus the plugin's tools once installed
(`daw_*` under `~/.hermes/plugins/ai-daw/`).

## Plugin contract (compatible with Hermes plugins)

- `plugin.yaml` declares name, version, entrypoint, and the tools it exposes;
  no side effects at import time.
- Tools are `daw_*`, take plain JSON-serialisable arguments, and return text or a
  path — never a live object the agent cannot serialise.
- Every tool names its project directory explicitly; no global "current project"
  hidden in process state.
- Failures are returned as readable errors with a remedy, not tracebacks, and a
  missing engine produces an install hint rather than a crash.
- The plugin can be removed by deleting its directory: projects live in the
  user's folder, not inside the plugin install.
- New engines conform to the same adapter base — if the Hermes contract and an
  engine's API disagree, the contract wins and the adapter absorbs the difference.

## Mission, stated as outcomes

- `hermes` can list, generate, regenerate, mute, and render tracks inside a
  project directory, with every action reversible.
- At least three engines work behind one interface: ACE-Step 1.5, a second local
  model, and one hosted fallback — so a dated engine or a dead GPU is an
  inconvenience, not a work stoppage.
- The LEGO pipeline survives: each generated layer conditions on the mix so far.
- A project is a folder of plain files (manifest + wavs + MIDI), so nothing is
  trapped in the plugin.
- The plugin installs and uninstalls cleanly under a stock Hermes plugin loader.

## Owns

- `bots/ai-daw/plugin/` — the working plugin: `plugin.yaml`, `plugin_tools.py`
  (seven `daw_*` tools), `daw/core.py` (manifest, versions, reference mix, stems,
  loudnorm mix), `daw/config.py`, and `daw/adapters/` (`base`, `registry`,
  `dryrun`, `acestep`, `replicate`). Twenty-eight tests in `bots/ai-daw/tests/`
  run the whole pipeline on synthesised audio, no GPU and no model weights.
- The plugin: `~/.hermes/plugins/ai-daw/{plugin.yaml,plugin_tools.py,adapters/,projects/}`.
- `adapters/<engine>.py` — one file per music model, same interface.
- Project format: `project.json` (bpm, key, sections, track list, seeds) + `stems/`.
- `bots/ai-daw/engines.md` — the model comparison that decides what gets adopted.

## Operating loop

1. **Project** — turn the conversation into `project.json`: bpm, key, section
   map (intro/verse/chorus/bridge/outro with bar counts). Ambiguity is asked
   about, not silently defaulted into the manifest.
2. **Layer** — generate one instrument at a time, conditioned on the current mix
   (drums → bass → harmony → lead → vocals). Each call records engine, model,
   seed, and prompt in the manifest.
3. **Audition** — write alternates to `stems/<track>/alt-N.wav`; never overwrite a
   keeper. A/B by loudness-matched playback, not by ear at different levels.
4. **Arrange** — place layers on the timeline; the plugin edits the manifest, the
   DAW UI reads it. One source of truth.
5. **Render** — stems (one per track, aligned, no master bus) + mix (with master).
   Then loudness-report the mix; -14 LUFS for streaming, -9 for club, state which.
6. **Adopt** — when a new model appears, add an adapter only if it beats the
   current one on a fixed eval: prompt adherence, musicality at 2 min, stem
   availability, latency, license.
7. **Log** — one line per session: what was generated, how long, what was kept.

## Skills

| Skill | When it loads | State |
|---|---|---|
| [[bots/ai-daw/skills/daw-plugin-scaffold/SKILL]] | creating or extending the Hermes plugin | written |
| [[bots/ai-daw/skills/music-model-adapter/SKILL]] | adding an engine | written |
| [[bots/ai-daw/skills/lego-arrangement/SKILL]] | running the layer-by-layer compose | written |

## Loops

| Loop | Schedule | State |
|---|---|---|
| [[bots/ai-daw/loops/engine-watch]] | monthly, 1st at 09:00 | spec |

## Hold points

- **Licenses.** ACE-Step DAW is AGPL-3.0-or-later and Riff's plugin ships inside
  Hermes (MIT). Keep the plugin a *client* of the DAW, not a copy of its source,
  or the license obligation changes. Check every model card before bundling weights.
- **Voice cloning / artist imitation** by name is refused outright.
- **Nothing publishes to a streaming service.** Export only.

## Needs from the operator

- Where the GPU lives: does ACE-Step run on omarchy (3090?) or does this container
  call a LAN endpoint? That decides local vs hosted-first.
- Whether the plugin must drive the existing React/Tone.js DAW UI or may own its
  own minimal player. Driving theirs is more work but keeps one interface.

## Log

- 2026-11-07 — bot seeded; adapter interface specified; ACE-Step 1.5 registered as baseline engine.
- 2026-11-08 — plugin implemented: manifest-driven projects, idempotent layer generation keyed on (engine, model, seed, prompt, bars), versioned alternates that never overwrite a keeper, a 32 kbps mono reference mix for conditioning, aligned stems, and one loudnorm pass with a loudness report. `dryrun` synthesises real audio via ffmpeg so the pipeline is testable without a GPU; `acestep` is a thin HTTP client that fails with an install hint rather than a traceback. 14 tests green.
- 2026-11-16 — brief coverage: ACE-Step explicitly framed as dated baseline; added the Hermes plugin contract (manifest, daw_* tools, explicit project dir, readable failures, removable install) and raised the engine target to ACE-Step + a second local model + a hosted fallback behind one adapter interface.
- 2026-11-16 — engine seam: `Engine` protocol (`name`, `capabilities`, `available() -> (bool, reason)`, `generate -> Artifact`), a registry with `engine: acestep|replicate|auto` selection, and a second real adapter — hosted Replicate (MusicGen by default, any slug by config). `auto` records the pick and the skipped reasons on the track; unavailable engines name the token or server that fixes them. ACE-Step's client path is unchanged; 28 tests green, including an end-to-end Replicate render against a stub HTTP API and an ACE-Step client test against a stub server.
