#!/usr/bin/env python3
"""Parallel model archive: many files at once, each resumable and size-verified.

Single-stream curl tops out around 56 MB/s here regardless of the link, so the
throughput win comes from running independent files concurrently rather than
from more connections per file. Work is ordered by expected value (usable quants
first) and dispatched to a fixed pool; a file already at its expected size is
skipped, and a partial file resumes where it stopped.

Usage: archive_parallel.py <root> [workers]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/models/archive")
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
LOG = ROOT / "archive.log"
BAD = ("imatrix", "vocab", "tokenizer", "embedding")

# (repo, kind) — usable quants first, giant raw weights last.
TARGETS = [
    ("bartowski/NousResearch_Arete-27B-GGUF", "quant"),
    ("abenzerps/Nanbeige4.3-33B-GSQ-RCO-GGUF", "gsq"),
    ("ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF", "gsq"),
    ("unsloth/Qwen3.6-35B-A3B-MTP-GGUF", "quant"),
    ("unsloth/Qwen3.5-35B-A3B-MTP-GGUF", "quant"),
    ("LiquidAI/LFM2.5-24B-A2B-GGUF", "quant"),
    ("unsloth/flint-GGUF", "quant"),
    ("dima6312/Flint-40B-A2.5B-abliterated-GGUF", "quant"),
    ("pfeifferj/GLM-5.3-Flash-GSQ-RCO-GGUF", "gsq"),
    ("peasantsmith/GLM-5.3-Flash-Maya-GGUF", "gsq"),
    ("ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF", "gsq"),
    ("ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF", "gsq"),
    ("ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-GGUF", "gsq"),
    ("stamsam/maple-preview-gguf", "quant"),
    ("nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-GGUF", "quant"),
    ("LiquidAI/LFM3-Omni-2B-GGUF", "quant"),
    ("Abiray/MiniMax-H3-Image-GGUF", "quant"),
    ("unsloth/MiniMax-H3-GGUF", "quant"),
    ("audio-cpp/MiniMax-Music3-GGUF", "quant"),
    ("Baekpica/Darwin-180B-RSI-Mixed-Quant-GGUF", "quant"),
    ("outsourc-e/Qwen3.8-27B-Unleashed-GGUF", "quant"),
    ("huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated-MTP-GGUF", "quant"),
    ("peculiar-ragdoll/Cyber-Tiel-Coder-35B-A3B-GGUF-MTP", "quant"),
    ("AtomicChat/LFM2.5-24B-A2B-Uncensored-GGUF", "quant"),
    ("AtomicChat/DeepSeek-V4.1-Flash-1017-Uncensored-GSQ-RCO-GGUF", "gsq"),
    ("Abiray/DeepSeek-V4.1-Flash-1017-Uncensored-GSQ-RCO-Coder-GGUF", "gsq"),
    ("orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF", "quant"),
    ("SargeDev/Arete-27B-Uncensored-V2-GGUF", "quant"),
    ("orcarouter/GLM-5.3-Flash-Uncensored-GGUF", "quant"),
    ("BoldingBuilds/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-Abliterated-24GB-GGUF", "quant"),
    ("Kanposer/maple-preview-speedy-colibri-int2", "quant"),
    ("deepgrove/maple-preview-GGUF", "quant"),
    ("Qwen/Qwen3.8-27B", "weights"),
    ("NousResearch/Arete-27B", "weights"),
    ("Qwen/Qwen3.6-35B-A3B", "weights"),
    ("Qwen/Qwen3.5-35B-A3B", "weights"),
    ("zai-org/GLM-5.3-Flash", "weights"),
    ("Nanbeige/Nanbeige4.3-33B", "weights"),
    ("deepseek-ai/DeepSeek-V4.1-Flash-1017", "weights"),
    ("Qwen/Qwen3.8-Flash-Next", "weights"),
    ("LiquidAI/LFM2.5-24B-A2B", "weights"),
    ("LiquidAI/LFM3-Omni-2B", "weights"),
    ("MiniMaxAI/MiniMax-H3", "weights"),
    ("MiniMaxAI/MiniMax-H3-Image", "weights"),
    ("MiniMaxAI/MiniMax-Music3", "weights"),
    ("nvidia/personaplex-7b-v1", "weights"),
    ("nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-BF16", "weights"),
    ("nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB", "weights"),
    ("thinkingmachines/Inkling-2-Small", "weights"),
    ("deepgrove/maple-preview", "weights"),
    ("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "weights"),
    ("RecursiveSI/flint", "weights"),
]


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ')} {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def tree(repo: str) -> list[dict]:
    url = f"https://huggingface.co/api/models/{repo}/tree/main?recursive=true"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:
            if attempt == 2:
                log(f"! list failed {repo}: {exc}")
                return []
            time.sleep(2)
    return []


def select(files: list[dict], kind: str) -> list[dict]:
    files = [f for f in files if f.get("type") == "file"]
    gguf = [f for f in files if f["path"].lower().endswith(".gguf")]
    safet = [f for f in files if f["path"].lower().endswith(".safetensors")]
    models = [f for f in gguf if not any(b in f["path"].lower() for b in BAD)]
    proj = [f for f in gguf if "mmproj" in f["path"].lower()]
    if not models:
        return safet
    tokens = (("iq3_s", "iq3_xxs", "iq3_m", "iq3_xs", "q3_k_m", "q3")
              if kind == "gsq"
              else ("q4_k_m", "q4_k_s", "iq4_xs", "q4_0", "q4"))
    chosen = None
    for token in tokens:
        hits = [f for f in models if token in f["path"].lower()]
        if hits:
            chosen = sorted(hits, key=lambda f: f["path"])[0]
            break
    if chosen is None:
        chosen = sorted(models, key=lambda f: f.get("size", 0) or 0)[0]
    picks = [chosen]
    match = re.match(r"^(.*)-0*1-of-(\d+)\.gguf$", chosen["path"], re.I)
    if match:
        prefix, count = match.group(1), int(match.group(2))
        picks = sorted(
            [f for f in models
             if re.match(rf"^{re.escape(prefix)}-0*\d+-of-{count}\.gguf$", f["path"], re.I)],
            key=lambda f: f["path"],
        )
    if proj:
        picks.append(proj[0])
    return picks


def download(repo: str, path: str, size: int) -> str:
    dest = ROOT / repo.split("/")[0] / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and size and dest.stat().st_size >= size * 0.995:
        return f"have {path}"
    began = time.monotonic()
    proc = subprocess.run(
        ["curl", "-L", "--retry", "8", "--retry-delay", "5", "--retry-all-errors",
         "-C", "-", "--connect-timeout", "30", "--max-time", "21600",
         "-o", str(dest), f"https://huggingface.co/{repo}/resolve/main/{path}"],
        capture_output=True, text=True, check=False,
    )
    got = dest.stat().st_size if dest.exists() else 0
    ok = proc.returncode == 0 and (not size or got >= size * 0.995)
    elapsed = max(time.monotonic() - began, 1)
    rate = (got / elapsed) / 2**20
    return (f"{'ok' if ok else 'FAIL'} {path} {got / 2**30:.2f} GiB "
            f"rc={proc.returncode} {rate:.1f} MB/s")


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    log(f"=== parallel archive start root={ROOT} workers={WORKERS}")

    queue: list[tuple[str, str, int]] = []
    for repo, kind in TARGETS:
        for entry in select(tree(repo), kind):
            queue.append((repo, entry["path"], int(entry.get("size", 0) or 0)))
    log(f"resolved {len(queue)} artefacts from {len(TARGETS)} repos")

    done = failed = 0
    began = time.monotonic()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(download, r, p, s): (r, p) for r, p, s in queue}
        for fut in as_completed(futures):
            try:
                log("  " + fut.result())
                if fut.result().startswith(("ok", "have")):
                    done += 1
                else:
                    failed += 1
            except Exception as exc:
                failed += 1
                log(f"  ERROR {futures[fut]}: {exc}")
    log(f"=== complete {done} ok / {failed} failed in {(time.monotonic() - began) / 60:.0f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
