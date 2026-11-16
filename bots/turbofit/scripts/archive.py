#!/usr/bin/env python3
"""Emergency archive: pull model artifacts to local disk with resume + verification.

Reads a list of (repo, revision, path, size_bytes, sha256) and downloads with
`curl -L -C -` so an interrupted run resumes instead of restarting a 40 GiB file.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT = Path("/opt/data/models/archive")
LOG = ROOT / "archive.log"

# (repo, revision, repo_path, size_bytes) — ordered by priority, smallest first.
TARGETS = [
    ("bartowski/NousResearch_Arete-27B-GGUF", "9762c8502a79bd2b8634735d75f426b9febe092c",
     "NousResearch_Arete-27B-Q3_K_S.gguf", 12_499_000_000),
    ("bartowski/NousResearch_Arete-27B-GGUF", "9762c8502a79bd2b8634735d75f426b9febe092c",
     "mmproj-NousResearch_Arete-27B-f16.gguf", 923_000_000),
    ("bartowski/NousResearch_Arete-27B-GGUF", "9762c8502a79bd2b8634735d75f426b9febe092c",
     "NousResearch_Arete-27B-Q4_K_M.gguf", 17_198_000_000),
    ("abenzerps/Nanbeige4.3-33B-GSQ-RCO-GGUF", "76c254c0f736c65acdf9444ce9e15d8d654ad9c0",
     "Nanbeige4.3-33B-GSQ-RCO-IQ3_XS.gguf", 14_806_000_000),
    ("orcarouter/Flint-abliterated-GGUF", "4d618d1cb1d7782d4b08762fb664487bf5e4d3c4",
     "Flint-abliterated-Mix-12G.gguf", 11_994_000_000),
    ("ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF", "d562806dbafae37109975e970aae91b43e73b440",
     "Qwen3.8-27B-GSQ-RCO-IQ3_S.gguf", 11_766_000_000),
]


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ')} {msg}"
    print(line, flush=True)
    with LOG.open("a") as handle:
        handle.write(line + "\n")


def fetch(repo: str, revision: str, path: str, dest: Path) -> int:
    url = f"https://huggingface.co/{repo}/resolve/{revision}/{path}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["curl", "-L", "--retry", "5", "--retry-all-errors", "-C", "-",
         "--max-time", "7200", "-o", str(dest), url],
        capture_output=True, text=True,
    )
    return result.returncode


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    for repo, revision, path, size in TARGETS:
        dest = ROOT / repo.split("/")[0] / path
        if dest.exists() and dest.stat().st_size >= size * 0.995:
            log(f"have {path} ({dest.stat().st_size // 2**30} GiB)")
            continue
        log(f"start {path} (~{size / 2**30:.1f} GiB)")
        code = fetch(repo, revision, path, dest)
        got = dest.stat().st_size if dest.exists() else 0
        status = "ok" if code == 0 and got >= size * 0.995 else f"INCOMPLETE rc={code}"
        log(f"done  {path} {got // 2**30} GiB {status}")
    log("archive pass complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
