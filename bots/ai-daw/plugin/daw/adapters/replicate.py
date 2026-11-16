"""Replicate adapter: any hosted music model behind one HTTP call.

ACE-Step is the baseline, not the ceiling. This adapter reaches Replicate's
predictions API (https://replicate.com/docs/reference/http) so a newer model -
Meta MusicGen by default - is a config value, not a rewrite:

    DAW_REPLICATE_TOKEN   required; https://replicate.com/account/api-tokens
    DAW_REPLICATE_MODEL   model slug, default "meta/musicgen"
    DAW_REPLICATE_API     API base, default https://api.replicate.com

It is honest about absence: ``available()`` returns False naming the missing
token, and ``generate()`` raises EngineUnavailable with the same remedy. It
never fabricates an audio path - the file on disk is whatever the API returned,
or the call fails.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .. import config
from .base import Artifact, Capabilities, EngineBase, EngineUnavailable

DEFAULT_API = "https://api.replicate.com"
DEFAULT_MODEL = "meta/musicgen"
PENDING = ("starting", "processing")


class ReplicateEngine(EngineBase):
    name = "replicate"
    model = DEFAULT_MODEL
    install_hint = (
        "set DAW_REPLICATE_TOKEN to a Replicate API token "
        "(create one at https://replicate.com/account/api-tokens); "
        "no package install is needed"
    )

    def __init__(self, token: str | None = None, base: str | None = None,
                 model: str | None = None, timeout_s: float | None = None,
                 poll_s: float | None = None) -> None:
        self.token = token if token is not None else _token()
        self.base = (base or config.setting("replicate_api", default=DEFAULT_API)).rstrip("/")
        self.model = model or str(config.setting("replicate_model", default=DEFAULT_MODEL))
        self.timeout_s = float(timeout_s or config.setting("replicate_timeout", default=300))
        self.poll_s = float(poll_s if poll_s is not None
                            else config.setting("replicate_poll", default=2.0))

    # -- readiness ---------------------------------------------------------
    def capabilities(self) -> Capabilities:
        return Capabilities(duration_s=120.0, vocals=False, stems=False,
                            bpm_key_conditioning=False, local=False,
                            license="depends on the model slug; check its card on Replicate")

    def available(self) -> tuple[bool, str]:
        if not self.token:
            return False, self.install_hint
        return True, ""

    # -- render ------------------------------------------------------------
    def generate(self, request: dict[str, Any]) -> Artifact:
        ok, reason = self.available()
        if not ok:
            raise EngineUnavailable(f"engine 'replicate' cannot render: {reason}")

        started = time.monotonic()
        payload = {"input": self._input(request)}
        prediction = self._post(f"/v1/models/{self.model}/predictions", payload)

        prediction = self._wait(prediction)
        status = str(prediction.get("status", ""))
        if status != "succeeded":
            detail = prediction.get("error") or status or "no status"
            return Artifact(ok=False, engine=self.name, model=self.model,
                            error=f"Replicate prediction {detail}",
                            hint="inspect the prediction at "
                                 f"{prediction.get('urls', {}).get('get', 'replicate.com')}")

        url = _output_url(prediction.get("output"))
        if not url:
            return Artifact(ok=False, engine=self.name, model=self.model,
                            error="Replicate returned no audio URL",
                            hint=f"model '{self.model}' may not produce audio; check its schema")

        dest = Path(request["output"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                body = response.read()
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            return Artifact(ok=False, engine=self.name, model=self.model,
                            error=f"could not download the render: {exc}",
                            hint="the output URL expires; retry the generation")
        if not body:
            return Artifact(ok=False, engine=self.name, model=self.model,
                            error="Replicate returned an empty file",
                            hint="retry; if it repeats, try another model slug")
        dest.write_bytes(body)

        return Artifact(ok=True, engine=self.name, model=self.model,
                        audio_paths=[str(dest)], stems=False,
                        seed_used=request.get("seed"),
                        cost=0.0,
                        elapsed_s=round(time.monotonic() - started, 3),
                        metadata={"prediction_id": prediction.get("id", ""),
                                  "model": self.model, "hosted": True,
                                  "total_time_s": prediction.get("metrics", {}).get("total_time")})

    def _input(self, request: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "prompt": str(request.get("prompt", "")),
            "duration": max(1, int(round(float(request.get("duration_s", 8))))),
        }
        if request.get("seed") is not None and os.environ.get("DAW_REPLICATE_SEND_SEED") == "1":
            payload["seed"] = int(request["seed"])
        extra = os.environ.get("DAW_REPLICATE_INPUT_JSON")
        if extra:
            try:
                parsed = json.loads(extra)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                payload.update(parsed)
        return payload

    def _headers(self) -> dict[str, str]:
        return {"authorization": f"Bearer {self.token}",
                "content-type": "application/json",
                "prefer": "wait"}

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        request = urllib.request.Request(
            f"{self.base}{path}", data=json.dumps(payload).encode(),
            headers=self._headers(), method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:300]
            return {"status": "failed", "error": f"HTTP {exc.code}: {body}"}
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            return {"status": "failed", "error": f"unreachable: {exc}"}

    def _wait(self, prediction: dict[str, Any]) -> dict[str, Any]:
        """Poll until the prediction leaves starting/processing or time runs out."""
        status = str(prediction.get("status", ""))
        if status not in PENDING:
            return prediction
        get_url = prediction.get("urls", {}).get("get")
        if not get_url:
            return {"status": "failed", "error": "prediction has no poll URL"}
        deadline = time.monotonic() + self.timeout_s
        while status in PENDING and time.monotonic() < deadline:
            time.sleep(self.poll_s)
            request = urllib.request.Request(get_url, headers=self._headers())
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    prediction = json.loads(response.read().decode() or "{}")
            except urllib.error.HTTPError as exc:
                return {"status": "failed", "error": f"poll HTTP {exc.code}"}
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                return {"status": "failed", "error": f"poll unreachable: {exc}"}
            status = str(prediction.get("status", ""))
        if status in PENDING:
            return {"status": "failed",
                    "error": f"timed out after {self.timeout_s:.0f}s",
                    "urls": prediction.get("urls", {})}
        return prediction


def _token() -> str:
    token = os.environ.get("DAW_REPLICATE_TOKEN")
    if token:
        return token
    return str(config.load().get("replicate_token", "") or "")


def _output_url(output: Any) -> str | None:
    """Replicate returns a URL, a list of URLs, or a dict - accept all three."""
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        for item in output:
            url = _output_url(item)
            if url:
                return url
        return None
    if isinstance(output, dict):
        for key in ("audio", "url", "output"):
            if isinstance(output.get(key), str):
                return output[key]
    return None
