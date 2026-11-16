"""Engine catalog and selection.

``resolve`` maps a name (including the spellings people actually type) to an
adapter. ``select`` answers the harder question: for ``engine: auto``, which
engine is usable *now* - and if none is, why not, one reason per engine.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from .base import Engine, availability

ALIASES = {
    "ace": "acestep",
    "ace-step": "acestep",
    "ace-step-1.5": "acestep",
    "acestep-1.5": "acestep",
    "dry": "dryrun",
    "hosted": "replicate",
}

# Preference order for `auto`: the baseline first, then the hosted fallback,
# then the ffmpeg stand-in. A GPU server that is up always wins.
AUTO_ORDER = ("acestep", "replicate", "dryrun")


def _acestep() -> Engine:
    from .acestep import AceStepEngine

    return AceStepEngine()


def _replicate() -> Engine:
    from .replicate import ReplicateEngine

    return ReplicateEngine()


def _dryrun() -> Engine:
    from .dryrun import DryRunEngine

    return DryRunEngine()


CATALOG: dict[str, Callable[[], Engine]] = {
    "acestep": _acestep,
    "replicate": _replicate,
    "dryrun": _dryrun,
}


class NoEngineAvailable(RuntimeError):
    """Every candidate was probed and every candidate said no."""

    def __init__(self, reasons: dict[str, str]):
        self.reasons = dict(reasons)
        super().__init__("no engine available")

    def remedy(self) -> str:
        if not self.reasons:
            return "no engines are registered"
        return "none of the engines are available - " + "; ".join(
            f"{name}: {reason or 'not available'}" for name, reason in self.reasons.items()
        )


def known(registry: dict[str, Any] | None = None) -> list[str]:
    return sorted(set(CATALOG) | set(registry or {}))


def resolve(name: str, registry: dict[str, Any] | None = None) -> Engine:
    """Adapter for ``name``; raises KeyError naming the known engines."""
    if registry and name in registry:
        return registry[name]
    canonical = ALIASES.get(name, name)
    if canonical in CATALOG:
        return CATALOG[canonical]()
    if registry:
        for key, engine in registry.items():
            if getattr(engine, "name", key) == name:
                return engine
    raise KeyError(f"unknown engine '{name}'; known: {', '.join(known(registry))}")


def select(requested: str, registry: dict[str, Any] | None = None,
           order: Iterable[str] | None = None) -> tuple[Engine, dict[str, str]]:
    """Pick the engine to use.

    An explicit name is resolved and returned unchecked - the caller reports
    its unavailability with the engine's own reason. ``auto`` probes candidates
    in order (an injected registry is preferred, then AUTO_ORDER) and returns
    the first available one plus the reasons the others were skipped; if none
    are available it raises NoEngineAvailable.
    """
    if requested and requested != "auto":
        return resolve(requested, registry), {}

    if order is not None:
        candidates: list[str] = list(order)
    elif registry:
        # Explicitly injected adapters are the caller's own candidates.
        candidates = list(registry) + [name for name in AUTO_ORDER if name not in registry]
    else:
        candidates = list(AUTO_ORDER)
    for name in (registry or {}):
        if name not in candidates:
            candidates.append(name)

    reasons: dict[str, str] = {}
    for name in candidates:
        try:
            engine = resolve(name, registry)
        except KeyError:
            continue
        ok, reason = availability(engine)
        if ok:
            return engine, reasons
        reasons[getattr(engine, "name", name)] = reason or getattr(engine, "install_hint", "")
    raise NoEngineAvailable(reasons)
