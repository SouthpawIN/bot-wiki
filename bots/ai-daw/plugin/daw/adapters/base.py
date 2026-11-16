"""Engine adapters: one file per music model, one interface for all of them.

The seam is deliberately small. An engine declares what it can do
(``capabilities``), whether it can do it right now (``available`` - a bool and a
reason, never a bare False), and how to render one layer (``generate`` ->
``Artifact``). Selection and configuration live in ``registry``; nothing here
imports a concrete backend, so adding a model is a new file, not an edit.

``health()`` survives as a compatibility shim for adapters written against the
0.1 interface; new adapters implement ``available()``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class Capabilities:
    duration_s: float
    vocals: bool
    stems: bool
    bpm_key_conditioning: bool
    local: bool
    license: str


@dataclass
class Artifact:
    """What an engine returns: paths and provenance, never audio bytes.

    ``ok=False`` always carries ``error`` and, where a fix exists, ``hint``.
    ``metadata`` is engine-specific provenance (engine name, model, seed,
    selection notes) and is copied into the project manifest.
    """

    ok: bool
    engine: str = ""
    model: str = ""
    audio_paths: list[str] = field(default_factory=list)
    stems: bool = False
    seed_used: int | None = None
    cost: float = 0.0
    elapsed_s: float = 0.0
    error: str = ""
    hint: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "engine": self.engine,
            "model": self.model,
            "audio_paths": list(self.audio_paths),
            "stems": self.stems,
            "seed_used": self.seed_used,
            "cost": self.cost,
            "elapsed_s": self.elapsed_s,
            "error": self.error,
            "hint": self.hint,
            "metadata": dict(self.metadata),
        }


class EngineUnavailable(RuntimeError):
    """Raised when a caller asks an engine to render while it cannot.

    The message names the configuration key or install command that fixes it.
    """


@runtime_checkable
class Engine(Protocol):
    name: str
    model: str
    install_hint: str

    def capabilities(self) -> Capabilities: ...
    def available(self) -> tuple[bool, str]: ...
    def generate(self, request: dict[str, Any]) -> Artifact: ...


# 0.1 spelled the interface MusicEngine. Keep the name importable.
MusicEngine = Engine


class EngineBase:
    """Default plumbing shared by the bundled adapters.

    Subclasses declare ``name``/``model``/``install_hint``, implement
    ``capabilities()`` and ``generate()``, and override ``available()`` if they
    need a probe. ``health()`` is the 0.1 spelling of the same question.
    """

    name = ""
    model = ""
    install_hint = ""

    def capabilities(self) -> Capabilities:  # pragma: no cover - abstract
        raise NotImplementedError

    def available(self) -> tuple[bool, str]:
        return True, ""

    def health(self) -> bool:
        return availability(self)[0]

    def generate(self, request: dict[str, Any]) -> Artifact:  # pragma: no cover
        raise NotImplementedError


def availability(engine: Any) -> tuple[bool, str]:
    """Ask any adapter - new or legacy - whether it can render now.

    Prefers ``available()``. Falls back to the 0.1 ``health()`` + ``install_hint``
    pair so third-party adapters and test doubles keep working unchanged.
    """
    probe = getattr(engine, "available", None)
    if callable(probe):
        ok, reason = probe()
        return bool(ok), str(reason or "")
    legacy = getattr(engine, "health", None)
    if callable(legacy):
        ok = bool(legacy())
        return ok, "" if ok else str(getattr(engine, "install_hint", ""))
    name = getattr(engine, "name", "?")
    return False, f"engine '{name}' implements neither available() nor health()"


def as_artifact(result: Any, *, fallback_name: str = "", fallback_model: str = "") -> Artifact:
    """Normalise a generate() result to Artifact (accepts plain dicts too)."""
    if isinstance(result, Artifact):
        return result
    if not isinstance(result, dict):
        return Artifact(ok=False, engine=fallback_name, model=fallback_model,
                        error=f"engine returned {type(result).__name__}, expected Artifact")
    known = {key: result[key] for key in Artifact.__dataclass_fields__ if key in result}
    known.setdefault("engine", fallback_name)
    known.setdefault("model", fallback_model)
    known.setdefault("ok", False)
    return Artifact(**known)


def get_engine(name: str, registry: dict[str, Any] | None = None) -> Engine:
    """Resolve an adapter by name. Unknown engines fail with a hint, not a stack."""
    from .registry import resolve

    return resolve(name, registry)
