"""Tests for execution/quality_gate.py (kit v1.71.3).

Liveness-audit finding A3: PRE_RETRO_SCENARIOS named two scenarios that
have never existed in test_methodology.py (invariant_regression,
completed_feature_hygiene), so `quality_gate.py --pre-retro` exited 2
("Unknown scenario(s)") on every run since v1.49.1 — the pre-commit
retro gate pointed users at a command that could not succeed. These
tests pin every gate scenario list to the live SCENARIOS registry.
"""
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / "execution"))

import quality_gate  # noqa: E402
import test_methodology  # noqa: E402

REGISTRY = {name for name, _ in test_methodology.SCENARIOS}


def test_pre_retro_scenarios_all_exist():
    phantom = set(quality_gate.PRE_RETRO_SCENARIOS) - REGISTRY
    assert not phantom, (
        f"PRE_RETRO_SCENARIOS names scenarios that don't exist: {phantom} — "
        "test_methodology exits 2 on unknown names, so the pre-retro gate "
        "can never pass"
    )


def test_checkpoint_scenarios_all_exist():
    phantom = set(quality_gate.CHECKPOINT_SCENARIOS) - REGISTRY
    assert not phantom, (
        f"CHECKPOINT_SCENARIOS names scenarios that don't exist: {phantom}"
    )


def test_scenario_lists_not_empty():
    assert quality_gate.PRE_RETRO_SCENARIOS
    assert quality_gate.CHECKPOINT_SCENARIOS
