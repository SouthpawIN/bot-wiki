"""The engine seam: conformance, honest unavailability, auto selection, provenance.

Two rules these tests enforce:

* no test downloads model weights or invents a render - stub bytes are written by
  a test engine or a stub HTTP endpoint and are labelled as stubs;
* an unavailable engine says what would fix it, and never returns ``ok=True``.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys

import pytest

PLUGIN = Path(__file__).parents[1] / "plugin"
sys.path.insert(0, str(PLUGIN))

from daw.adapters import (  # noqa: E402
    Artifact,
    Capabilities,
    Engine,
    EngineUnavailable,
    NoEngineAvailable,
    availability,
    known,
    resolve,
    select,
)
from daw.adapters.acestep import AceStepEngine  # noqa: E402
from daw.adapters.dryrun import DryRunEngine  # noqa: E402
from daw.adapters.replicate import ReplicateEngine  # noqa: E402
from daw.core import Project  # noqa: E402

STUB_BYTES = b"STUB-AUDIO-NOT-A-REAL-RENDER|engine=stub|deterministic fixture bytes"


@pytest.fixture(autouse=True)
def clean_engine_config(monkeypatch, tmp_path: Path) -> None:
    """No ambient engine choice or token may leak into these tests."""
    for key in ("DAW_ENGINE", "DAW_REPLICATE_TOKEN", "DAW_REPLICATE_MODEL",
                "DAW_REPLICATE_API", "DAW_ACESTEP_URL", "DAW_REPLICATE_INPUT_JSON"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DAW_CONFIG", str(tmp_path / "no-config.json"))


class StubEngine:
    """A test engine: writes deterministic stub bytes, labelled as such."""

    name = "stub"
    model = "stub-model-1"
    install_hint = "the stub engine needs nothing; it is a test double"

    def capabilities(self) -> Capabilities:
        return Capabilities(duration_s=8.0, vocals=False, stems=False,
                            bpm_key_conditioning=False, local=True, license="test-only")

    def available(self) -> tuple[bool, str]:
        return True, ""

    def generate(self, request: dict) -> Artifact:
        out = Path(request["output"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(STUB_BYTES)
        return Artifact(ok=True, engine=self.name, model=self.model,
                        audio_paths=[str(out)], seed_used=request.get("seed"),
                        elapsed_s=0.0, metadata={"stub": True, "engine": self.name})


class MissingEngine:
    """Available=False with a specific remedy, so the message can be asserted."""

    def __init__(self, name: str, remedy: str) -> None:
        self.name = name
        self.model = f"{name}-model"
        self.install_hint = remedy
        self.remedy = remedy

    def capabilities(self) -> Capabilities:
        return Capabilities(duration_s=30.0, vocals=False, stems=False,
                            bpm_key_conditioning=False, local=False, license="test-only")

    def available(self) -> tuple[bool, str]:
        return False, self.remedy

    def generate(self, request: dict) -> Artifact:  # pragma: no cover - never reached
        raise AssertionError("an unavailable engine must not be asked to generate")


@pytest.fixture()
def project(tmp_path: Path) -> Project:
    return Project.create(tmp_path / "projects", "demo", bpm=120, key="A minor",
                          sections=[{"name": "main", "bars": 2}])


# -- 1. protocol conformance ------------------------------------------------
@pytest.mark.parametrize("name", ["acestep", "replicate", "dryrun"])
def test_bundled_engines_conform_to_the_engine_protocol(name: str) -> None:
    engine = resolve(name)
    assert isinstance(engine, Engine), f"{name} must satisfy the Engine protocol"
    assert engine.name == name and engine.model, "name and model are part of the contract"

    caps = engine.capabilities()
    assert isinstance(caps, Capabilities)
    assert caps.duration_s > 0 and isinstance(caps.local, bool) and caps.license

    ok, reason = engine.available()
    assert isinstance(ok, bool) and isinstance(reason, str)
    assert ok is False or reason == "", "an available engine owes no excuse"


def test_aliases_and_unknown_names_are_readable() -> None:
    assert resolve("ace-step").name == "acestep"
    assert resolve("hosted").name == "replicate"
    assert "acestep" in known() and "replicate" in known()
    with pytest.raises(KeyError, match="known:.*replicate"):
        resolve("suno-magic")


# -- 2. honest unavailability ------------------------------------------------
def test_replicate_without_a_token_names_the_exact_fix(tmp_path: Path) -> None:
    engine = ReplicateEngine(token="", base="http://127.0.0.1:9")
    ok, reason = engine.available()
    assert ok is False
    assert "DAW_REPLICATE_TOKEN" in reason and "replicate.com" in reason

    dest = tmp_path / "never.wav"
    with pytest.raises(EngineUnavailable, match="DAW_REPLICATE_TOKEN"):
        engine.generate({"prompt": "x", "duration_s": 4, "output": str(dest)})
    assert not dest.exists(), "a failed engine must not leave a file behind"


def test_layer_generation_returns_the_install_step_not_a_traceback(project: Project) -> None:
    result = project.generate_layer(instrument="drums", prompt="beat", engine="replicate")
    assert result["ok"] is False
    assert "DAW_REPLICATE_TOKEN" in result["hint"]
    assert project.status()["tracks"] == [], "nothing was generated, so nothing is recorded"


def test_dryrun_is_unavailable_without_ffmpeg(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    ok, reason = DryRunEngine().available()
    assert ok is False and "ffmpeg" in reason


# -- 3. auto selection -------------------------------------------------------
def test_auto_picks_the_first_available_engine_and_records_the_pick(project: Project) -> None:
    registry = {"offline-host": MissingEngine("offline-host", "start the host, then retry"),
                "stub": StubEngine()}
    result = project.generate_layer(instrument="drums", prompt="beat",
                                    engine="auto", engines=registry)
    assert result["ok"] is True, result
    assert result["engine"] == "stub", "auto skips the unavailable engine"
    assert result["selection"] == {
        "requested": "auto",
        "picked": "stub",
        "skipped": {"offline-host": "start the host, then retry"},
    }
    manifest = json.loads((project.root / "project.json").read_text())
    track = manifest["tracks"][0]
    assert track["engine"] == "stub" and track["engine_requested"] == "auto"


def test_auto_with_no_engine_available_lists_every_reason(project: Project,
                                                         monkeypatch) -> None:
    monkeypatch.setattr("daw.adapters.registry.CATALOG", {})
    monkeypatch.setattr("daw.adapters.registry.AUTO_ORDER", ())
    registry = {"ace": MissingEngine("ace", "run the ACE-Step server"),
                "cloud": MissingEngine("cloud", "export DAW_REPLICATE_TOKEN")}
    result = project.generate_layer(instrument="drums", prompt="beat",
                                    engine="auto", engines=registry)
    assert result["ok"] is False
    assert result["error"] == "no engine available for engine=auto"
    assert "run the ACE-Step server" in result["hint"]
    assert "export DAW_REPLICATE_TOKEN" in result["hint"]
    assert set(result["engines"]) == {"ace", "cloud"}


def test_select_raises_with_reasons_when_nothing_is_available(monkeypatch) -> None:
    monkeypatch.setattr("daw.adapters.registry.CATALOG", {})
    monkeypatch.setattr("daw.adapters.registry.AUTO_ORDER", ())
    registry = {"a": MissingEngine("a", "hint-a"), "b": MissingEngine("b", "hint-b")}
    with pytest.raises(NoEngineAvailable) as caught:
        select("auto", registry)
    assert caught.value.reasons == {"a": "hint-a", "b": "hint-b"}


def test_configured_engine_is_used_when_the_call_names_none(project: Project,
                                                            monkeypatch) -> None:
    monkeypatch.setenv("DAW_ENGINE", "auto")
    registry = {"stub": StubEngine()}
    result = project.generate_layer(instrument="bass", prompt="sub", engines=registry)
    assert result["engine"] == "stub" and result["engine_requested"] == "auto"


# -- 4. provenance -----------------------------------------------------------
def test_a_render_carries_the_engine_name_in_its_metadata(project: Project) -> None:
    result = project.generate_layer(instrument="lead", prompt="hook", engine="stub",
                                    engines={"stub": StubEngine()})
    assert result["engine"] == "stub"
    assert result["metadata"]["engine"] == "stub"
    assert result["model"] == "stub-model-1"

    track = json.loads((project.root / "project.json").read_text())["tracks"][0]
    assert track["engine"] == "stub" and track["model"] == "stub-model-1"
    assert track["metadata"]["stub"] is True
    assert project.status()["tracks"][0]["engine"] == "stub"


# -- 5. the ACE-Step path still works ---------------------------------------
class _StubServer:
    """A tiny HTTP server; routes are handler functions of (handler, body)."""

    def __init__(self, routes: dict) -> None:
        outer = self
        self.routes = routes
        self.calls: list[tuple[str, str, dict]] = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:  # keep pytest output clean
                pass

            def _serve(self, method: str) -> None:
                length = int(self.headers.get("content-length") or 0)
                raw = self.rfile.read(length) if length else b""
                body = json.loads(raw) if raw else {}
                outer.calls.append((method, self.path, body))
                route = outer.routes.get((method, self.path.split("?")[0]))
                if route is None:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"{}")
                    return
                status, payload = route(body)
                data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:
                self._serve("GET")

            def do_POST(self) -> None:
                self._serve("POST")

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self) -> "_StubServer":
        self.thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def test_acestep_client_still_moves_audio_and_declares_its_capabilities(tmp_path: Path) -> None:
    served = tmp_path / "server-render.wav"

    def generate(body: dict):
        served.write_bytes(STUB_BYTES)  # stands in for the server's file
        return 200, {"audio_path": str(served), "cost": 0.0}

    with _StubServer({("GET", "/config"): lambda body: (200, {"ok": True}),
                      ("POST", "/generate"): generate}) as server:
        engine = AceStepEngine(url=server.base)
        assert engine.available() == (True, "")
        assert engine.capabilities().local is True
        dest = tmp_path / "out" / "drums.wav"
        artifact = engine.generate({"prompt": "beat", "duration_s": 4, "seed": 11,
                                    "output": str(dest)})

    assert artifact.ok and artifact.engine == "acestep"
    assert dest.read_bytes() == STUB_BYTES
    assert artifact.seed_used == 11


def test_replicate_renders_through_core_against_a_stub_api(project: Project,
                                                           tmp_path: Path) -> None:
    """The real adapter code path, end to end: POST -> poll -> download."""
    state = {"polls": 0}
    routes: dict = {}

    with _StubServer(routes) as server:
        def create(body: dict):
            return 201, {"id": "pred-1", "status": "starting",
                         "urls": {"get": f"{server.base}/v1/predictions/pred-1"}}

        def poll(body: dict):
            state["polls"] += 1
            return 200, {"id": "pred-1", "status": "succeeded",
                         "output": f"{server.base}/files/render.wav",
                         "metrics": {"total_time": 12.5}}

        routes.update({
            ("POST", "/v1/models/meta/musicgen/predictions"): create,
            ("GET", "/v1/predictions/pred-1"): poll,
            ("GET", "/files/render.wav"): lambda body: (200, STUB_BYTES),
        })

        engine = ReplicateEngine(token="test-token", base=server.base,
                                 model="meta/musicgen", poll_s=0.01, timeout_s=5)
        result = project.generate_layer(instrument="harmony", prompt="warm pad",
                                        seed=5, engine="replicate",
                                        engines={"replicate": engine})

        posted = [call for call in server.calls if call[0] == "POST"]
        assert posted and posted[0][2]["input"]["prompt"] == "warm pad"

    assert result["ok"] is True, result
    assert result["engine"] == "replicate"
    assert result["metadata"]["prediction_id"] == "pred-1"
    stem = Path(result["path"])
    assert (project.root / stem).read_bytes() == STUB_BYTES
    assert state["polls"] >= 1, "starting predictions are polled, not trusted"
