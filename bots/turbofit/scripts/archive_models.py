#!/usr/bin/env python3
"""Emergency model archive: fetch the weights we catalogued, smallest-useful first.

Selection policy:
  * GSQ-RCO quant repos  -> the best Q3 the repo ships (IQ3_S > IQ3_XXS > Q3_K_M)
  * any other quant repo -> Q4_K_M (else Q4_K_S / IQ4_XS / Q4_0)
  * weights-only repos   -> every safetensors shard

Never picks imatrix / vocab / tokenizer / embedding blobs; adds exactly one
mmproj where the repo has one. Downloads resume (-C -) and are size-verified.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/models/archive")
LOG = ROOT / "archive.log"
BAD = ("imatrix", "vocab", "tokenizer", "embedding")

# (repo, kind) in priority order: usable quants first, giant weights last.
TARGETS = [
    ("bartowski/NousResearch_Arete-27B-GGUF", "quant"),
    ("abenzerps/Nanbeige4.3-33B-GSQ-RCO-GGUF", "gsq"),
    ("ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF", "gsq"),
    ("unsloth/Qwen3.6-35B-A3B-MTP-GGUF", "quant"),
    ("unsloth/Qwen3.5-35B-A3B-MTP-GGUF", "quant"),
    ("LiquidAI/LFM2.5-24B-A2B-GGUF", "quant"),
    ("unsloth/flint-GGUF", "quant"),
    ("orcarouter/Flint-abliterated-GGUF", "quant"),
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
    ("ProCreations/maple-preview-webgpu-v2", "weights"),
    ("Qwen/Qwen3.8-27B", "weights"),
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
    ("nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B", "weights"),
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
                log(f"  ! list failed {repo}: {exc}")
                return []
            time.sleep(3)
    return []


def select(files: list[dict], kind: str) -> list[dict]:
    files = [f for f in files if f.get("type") == "file"]
    gguf = [f for f in files if f["path"].lower().endswith(".gguf")]
    safet = [f for f in files if f["path"].lower().endswith(".safetensors")]
    models = [f for f in gguf if not any(b in f["path"].lower() for b in BAD)]
    proj = [f for f in gguf if "mmproj" in f["path"].lower()]

    if not models:
        return safet  # a weights-only repo

    if kind == "gsq":
        tokens = ("iq3_s", "iq3_xxs", "iq3_m", "iq3_xs", "q3_k_m", "q3")
    else:
        tokens = ("q4_k_m", "q4_k_s", "iq4_xs", "q4_0", "q4")
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
        picks = [f for f in models
                 if re.match(rf"^{re.escape(prefix)}-0*\d+-of-{count}\.gguf$", f["path"], re.I)]
        picks.sort(key=lambda f: f["path"])
    if proj:
        picks.append(proj[0])
    return picks


def download(repo: str, path: str, size: int) -> tuple[bool, float]:
    dest = ROOT / repo.split("/")[0] / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and size and dest.stat().st_size >= size * 0.995:
        log(f"  have {path}")
        return True, 0.0
    url = f"https://huggingface.co/{repo}/resolve/main/{path}"
    log(f"  start {path} (~{size / 2**30:.1f} GiB)")
    began = time.monotonic()
    proc = subprocess.run(
        ["curl", "-L", "--retry", "8", "--retry-delay", "5", "--retry-all-errors",
         "-C", "-", "--connect-timeout", "30", "--max-time", "21600",
         "-o", str(dest), url],
        capture_output=True, text=True, check=False,
    )
    got = dest.stat().st_size if dest.exists() else 0
    ok = proc.returncode == 0 and (not size or got >= size * 0.995)
    log(f"  {'ok' if ok else 'FAIL'} {path} {got / 2**30:.2f} GiB rc={proc.returncode} "
        f"in {time.monotonic() - began:.0f}s")
    return ok, (time.monotonic() - began)


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    log(f"=== archive start root={ROOT} repos={len(TARGETS)}")
    done = failed = 0
    for repo, kind in TARGETS:
        log(f"repo {repo} [{kind}]")
        picks = select(tree(repo), kind)
        if not picks:
            log("  ! nothing selectable - skipped")
            failed += 1
            continue
        for entry in picks:
            path = entry["path"]
            size = int(entry.get("size", 0) or 0)
            ok, _ = download(repo, path, size)
            done += 1 if ok else 0
            failed += 0 if ok else 1
    log(f"=== archive complete: {done} ok, {failed} failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
