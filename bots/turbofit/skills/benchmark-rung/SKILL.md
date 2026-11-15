---
name: benchmark-rung
description: Turn a campaign measurement into a `measured` fit rung, with evidence.
version: 1.0.0
author: TurboSouth
license: MIT
metadata:
  hermes:
    tags: [turbofit, benchmark, campaign, fit-lists, evidence]
---

# Benchmark rung

Use when a rung has to move from `candidate` to `measured`, or when someone asks
"does that model actually run at that speed on that box". The campaign measures;
this skill only transcribes. A tok/s number that did not come out of a campaign
evidence bundle has no place in a fit list.

## Procedure

1. **Name the cell before naming a number.** A rung is measured by exactly one
   campaign cell in `bots/turbofit/benchmark-campaign.md`, and the cell's anchor
   is the configuration id the campaign uses:
   `<model>-<quant>-<drafter>-<ctx>`, e.g. `qwen-3-8-27b-q4-k-m-auto-64k`,
   `...-dflash2-auto-262k`, `...-mtp-maple-preview-20b-a1b-tq2-0-128k`.
   ```bash
   grep -n 'id="qwen-3-8-27b-q4-k-m-auto-262k"' bots/turbofit/benchmark-campaign.md
   ```
   No cell → nothing to measure to. Add the catalog variant and regenerate the
   campaign (`model-matrix-add`), or record the gap as a waiver. Never invent an
   anchor to make a rung look measured.

2. **Read the row's prerequisites, not its luck.**
   ```bash
   cd ~/turbofit && PYTHONPATH=src:. scripts/turbofit-catalog-campaign status
   ```
   `waiting_download`, `waiting_memory`, `waiting_runtime` are different
   prerequisites, not model failures. Each names an action: install the artifact
   (`scripts/install-native-runtimes`, `scripts/download-models.py`), free host
   memory for the offload planner, or install the family's engine binary. Act on
   that one thing, or leave the cell `[ ]` and say which prerequisite is missing.
   Running the row by hand to "just get a number" is the failure this skill exists
   to prevent.

3. **Run the campaign, not a server.** `run` is resumable and leases the
   production service before it clears the GPU, so a manual `llama-server` launch
   collides with the controller and produces evidence no other row can be compared
   against.
   ```bash
   PYTHONPATH=src:. scripts/turbofit-catalog-campaign run        # resume/next rows
   PYTHONPATH=src:. scripts/turbofit-catalog-campaign status    # progress
   ```
   A row only becomes eligible when its prerequisites are satisfied; a failure is
   retried with bounded backoff and stays unresolved. An arbitrary attempt count
   never converts failure into completion.

4. **Read the evidence bundle.** Under
   `references/results/catalog-campaign/<row>/<timestamp>/`, and only when all nine
   conditions hold: artifact verified immutable, exact recipe compiled, requested
   context verified, main + auxiliary healthy, non-empty output, throughput **and**
   peak memory captured, runtime string captured, process shut down, post-run
   memory clear verified. The bundle binds the hardware fingerprint — OS/arch,
   host RAM, accelerator UUIDs, PCI topology, per-device memory, compute
   capability, driver revision, topology key — and the raw result's SHA-256.
   The admissible number is `effective_output_tokens_per_second` in that result,
   with `quality_pass_rate` and `context_pass_rate` at 1.0. `status=pass` on a
   suite that did not exercise the requested context is not a measurement of that
   context.

5. **Transcribe, don't summarise.** In `references/fit-lists.json`, on the rung
   that this cell is evidence for:
   ```json
   "measured": {
     "tok_s": 34.2,
     "context": 262144,
     "cell": "qwen-3-8-27b-q4-k-m-auto-262k",
     "evidence_sha256": "<raw result sha256 from the bundle>",
     "hardware": "<topology key from the bundle>",
     "date": "2026-11-15"
   },
   "note": "…; measured 34.2 tok/s at 262K on <topology key>"
   ```
   - The tok/s in `note` must equal `measured.tok_s` — `release-gate` stage 2
     reads both, and a numeric tok/s in `note` with no matching checked cell is a
     FAIL.
   - `context` is the deadline the cell actually ran at, and may not exceed the
     largest checked cell for that model+quant.
   - One rung, one cell. A second measurement **replaces** the first: record the
     newer bundle, do not keep the best of several runs.
   - The number is attributed to `hardware`. A 3090 row does not describe an
     R9700 or a unified-memory host; there is no "typical" tok/s.
   - Drafters are not interchangeable: a `dflash2` cell and an `mtp` cell are two
     measurements, not a speedup claim. `DFlash2` is the default drafter, MTP wins
     for `parallel>=2`, non-Qwen families and the split engine — record which one
     the rung will actually serve.

6. **Check the cell in the same commit.** Flip `- [ ]` → `- [x]` on that anchor
   only, never on a cell whose bundle you did not just open, and never by
   un-checking a neighbour. Duplicate anchors are a FAIL because two rows would
   claim one measurement.

7. **Re-run the gate arithmetic before claiming it.**
   ```bash
   cd "$WIKI"   # bot-wiki clone
   checked=$(grep -c '^- \[x\]' bots/turbofit/benchmark-campaign.md)
   waived=$(grep -c '^- \[-\]' bots/turbofit/benchmark-campaign.md)
   total=$(grep -c '^- \[[ x-]\]' bots/turbofit/benchmark-campaign.md)
   echo "coverage $checked/$total, waived $waived"
   ```
   Coverage must not fall below the previous tag's count, and one line must
   report `coverage n/1165 (+delta), waived n, measured-rung mismatches 0`.

8. **Unservable cells get waived, not forgotten.** `- [-]` plus one row in the
   `## Waivers` table of `bots/turbofit/matrix.md`: anchor, date, reason (no
   hardware, no artifact, family dropped). Never delete a cell and never leave a
   dead one `[ ]` "because it might run later".

## Refusals

- No evidence bundle → no `measured` field, and the cell stays `[ ]`.
- A number from a vendor chart, a README, or another machine → refuse, and say
  which hardware it would have described.
- Promotion to a ladder winner is a campaign decision, never a catalog edit; the
  band default in `local_main_for_vram_gb` / `speed_main_for_vram_gb` /
  `shared_main_for_total_memory_gb` does not move because one cell got fast.
- Never measure a `waiting_*` row by hand to unblock a release; that turns a
  missing prerequisite into a false claim.

## Stop condition

Stop at the first failing gate and report the anchor and the failing condition.
An honest `0/1,165` with every rung labelled `candidate` is a fine release; a
green board with one unsupported number is not.
