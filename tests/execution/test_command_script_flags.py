"""Command-doc -> script flag-signature consistency (kit v1.71.3).

Liveness-audit finding A4: /hq's command doc passed `--source auto` to
build_hq.py, whose argparse has no such flag — every /hq run exited 2.
A command doc is orchestration prose; nothing executes it until a user
invokes the command, so a drifted flag is invisible to pytest unless
pinned. This test extracts every --flag a command doc passes to a kit
script and asserts the script's argparse actually defines it.
"""
import re
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]

# (command doc, script it invokes, script path)
PINNED = [
    ("global-commands/hq.md", "build_hq.py", "global-scripts/build_hq.py"),
]


def _flags_passed(doc_text, script_name):
    flags = set()
    for line in doc_text.splitlines():
        if script_name in line:
            flags.update(re.findall(r"(--[a-z][a-z0-9-]*)", line))
    return flags


def _flags_defined(script_text):
    return set(re.findall(r"add_argument\(\s*['\"](--[a-z][a-z0-9-]*)['\"]", script_text))


def test_command_docs_pass_only_real_flags():
    for doc_rel, script_name, script_rel in PINNED:
        doc = (KIT / doc_rel).read_text()
        script = (KIT / script_rel).read_text()
        passed = _flags_passed(doc, script_name)
        assert passed, f"{doc_rel} no longer invokes {script_name} — update PINNED"
        defined = _flags_defined(script)
        unknown = passed - defined
        assert not unknown, (
            f"{doc_rel} passes {sorted(unknown)} to {script_name}, which its "
            f"argparse does not define (defined: {sorted(defined)})"
        )
