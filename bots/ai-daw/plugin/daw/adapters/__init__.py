"""Adapter registry for the AI DAW plugin.

Import the seam from here: ``Engine``/``EngineBase`` to implement a backend,
``available_engines``/``select`` to ask which backend can run now.
"""
from .base import (
    Artifact,
    Capabilities,
    Engine,
    EngineBase,
    EngineUnavailable,
    MusicEngine,
    as_artifact,
    availability,
    get_engine,
)
from .registry import ALIASES, AUTO_ORDER, CATALOG, NoEngineAvailable, known, resolve, select

__all__ = [
    "ALIASES",
    "AUTO_ORDER",
    "Artifact",
    "CATALOG",
    "Capabilities",
    "Engine",
    "EngineBase",
    "EngineUnavailable",
    "MusicEngine",
    "NoEngineAvailable",
    "as_artifact",
    "availability",
    "get_engine",
    "known",
    "resolve",
    "select",
]
