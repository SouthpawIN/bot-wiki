"""Shared pytest configuration.

The YouTube bot renders real video with ffmpeg; a single assembly test takes
minutes. They stay in the suite (they are the only proof the pipeline produces
a playable file) but are deselected by default so ordinary runs stay fast.
Run them with `pytest --runslow`.
"""
from __future__ import annotations

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests that render real media with ffmpeg",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: renders real media via ffmpeg")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip = pytest.mark.skip(reason="slow ffmpeg render; use --runslow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)
