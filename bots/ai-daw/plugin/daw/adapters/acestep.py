"""ACE-Step adapter: a thin client over a local ACE-Step server.

This wraps the real API; it does not reimplement inference. Point it at the
ACE-Step server with DAW_ACESTEP_URL (default http://127.0.0.1:7860 for the
ACE-Step Gradio API).

0.1 behaviour is preserved: the engine returns ``ok=False`` with a readable
reason when the server is down rather than raising.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .base import Artifact, Capabilities, EngineBase

DEFAULT_URL = "http://127.0.0.1:7860"
TIMEOUT_S = float(os.environ.get("DAW_ACESTEP_TIMEOUT", "600"))


class AceStepEngine(EngineBase):
    name = "acestep"
    model = os.environ.get("DAW_ACESTEP_MODEL", "acestep-v1_5")
    install_hint = (
        "start the ACE-Step server (see SouthpawIN/ACE-Step-DAW), then set "
        "DAW_ACESTEP_URL; the plugin is a client and does not bundle weights"
    )

    def __init__(self, url: str | None = None) -> None:
        self.url = (url or os.environ.get("DAW_ACESTEP_URL") or DEFAULT_URL).rstrip("/")

    def capabilities(self) -> Capabilities:
        return Capabilities(duration_s=240.0, vocals=True, stems=False,
                            bpm_key_conditioning=True, local=True,
                            license="see the ACE-Step model card")

    def available(self) -> tuple[bool, str]:
        if self._probe():
            return True, ""
        return False, f"no ACE-Step server answered at {self.url}; {self.install_hint}"

    def _probe(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.url}/config", timeout=5) as response:
                return response.status == 200
        except (urllib.error.URLError, OSError, TimeoutError):
            return False

    def generate(self, request: dict[str, Any]) -> Artifact:
        started = time.monotonic()
        payload = {
            "prompt": request.get("prompt", ""),
            "lyrics": request.get("lyrics", ""),
            "duration": int(float(request.get("duration_s", 30))),
            "bpm": int(request.get("bpm", 120)),
            "key": request.get("key", ""),
            "seed": int(request.get("seed", 0)),
            "audio_reference": request.get("reference") or None,
        }
        body = json.dumps(payload).encode()
        call = urllib.request.Request(
            f"{self.url}/generate", data=body,
            headers={"content-type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(call, timeout=TIMEOUT_S) as response:
                result = json.loads(response.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            return Artifact(ok=False, engine=self.name, model=self.model,
                            error=f"ACE-Step HTTP {exc.code}",
                            hint=exc.read().decode(errors="replace")[:200])
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            return Artifact(ok=False, engine=self.name, model=self.model,
                            error=f"ACE-Step unreachable: {exc}", hint=self.install_hint)

        produced = result.get("audio_path") or result.get("path")
        if not produced:
            return Artifact(ok=False, engine=self.name, model=self.model,
                            error="ACE-Step returned no audio path",
                            hint="check the server log; the API shape may have changed")

        dest = Path(request["output"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        source = Path(produced)
        if not source.exists():
            return Artifact(ok=False, engine=self.name, model=self.model,
                            error=f"ACE-Step reported a missing file: {produced}",
                            hint="server and client must share a filesystem, or return a URL")
        if dest.exists():
            dest.unlink()
        source.replace(dest)
        return Artifact(ok=True, engine=self.name, model=self.model,
                        audio_paths=[str(dest)], stems=False,
                        seed_used=payload["seed"], cost=result.get("cost", 0.0),
                        elapsed_s=round(time.monotonic() - started, 3),
                        metadata={"server": self.url})
