#!/usr/bin/env python3
"""Validate DOE Proof scorecards against scorecard.schema.json.

Dependency-free: implements a focused structural check of the v1.0 contract so it
runs anywhere (no pip). If `jsonschema` is installed, ALSO runs full Draft-07
validation for extra rigor.

Usage:
    python3 validate.py <file-or-dir> [more ...]
Exit 0 if all valid, 1 if any invalid, 2 on usage error.
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "scorecard.schema.json")
KINDS = {"framework-benchmark", "project-metrics"}

def is_num(x): return isinstance(x, (int, float)) and not isinstance(x, bool)
def is_int(x): return isinstance(x, int) and not isinstance(x, bool)

def check(doc, path, errors):
    def e(msg): errors.append(f"{path}: {msg}")
    if not isinstance(doc, dict):
        e("top-level must be an object"); return
    for k in ("schemaVersion", "kind", "project", "generatedAt"):
        if k not in doc: e(f"missing required field '{k}'")
    sv = doc.get("schemaVersion")
    if sv is not None and not (isinstance(sv, str) and sv.startswith("1.")):
        e(f"schemaVersion must be '1.x', got {sv!r}")
    kind = doc.get("kind")
    if kind not in KINDS:
        e(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    proj = doc.get("project")
    if isinstance(proj, dict):
        for k in ("id", "name"):
            if k not in proj: e(f"project missing '{k}'")
    elif proj is not None:
        e("project must be an object")
    if kind == "framework-benchmark" and "catchRate" not in doc:
        e("framework-benchmark requires 'catchRate'")
    if kind == "project-metrics" and "dora" not in doc:
        e("project-metrics requires 'dora'")
    cr = doc.get("catchRate")
    if isinstance(cr, dict):
        for k in ("injected", "caught", "rate"):
            if k not in cr: e(f"catchRate missing '{k}'")
        if is_int(cr.get("injected")) and is_int(cr.get("caught")) and cr["caught"] > cr["injected"]:
            e("catchRate.caught exceeds injected")
        if is_num(cr.get("rate")) and not (0 <= cr["rate"] <= 1):
            e("catchRate.rate must be between 0 and 1")
    elif cr is not None:
        e("catchRate must be an object")
    d = doc.get("dora")
    if isinstance(d, dict):
        for k in ("changeFailureRate", "reworkRate"):
            if k not in d: e(f"dora missing '{k}'")
            elif is_num(d.get(k)) and not (0 <= d[k] <= 1):
                e(f"dora.{k} must be between 0 and 1")
    elif d is not None:
        e("dora must be an object")

def jsonschema_check(doc, path, errors):
    try:
        import jsonschema
    except ImportError:
        return
    try:
        with open(SCHEMA_PATH) as f: schema = json.load(f)
        jsonschema.validate(doc, schema)
    except jsonschema.ValidationError as ex:
        errors.append(f"{path}: jsonschema: {ex.message}")
    except Exception:
        pass

def collect(args):
    files = []
    for a in args:
        if os.path.isdir(a):
            files += [os.path.join(a, n) for n in sorted(os.listdir(a)) if n.endswith(".json")]
        else:
            files.append(a)
    return files

def main(argv):
    if len(argv) < 2:
        print("usage: validate.py <file-or-dir> [...]"); return 2
    files = collect(argv[1:])
    if not files:
        print("no .json files found"); return 2
    errors = []
    for fp in files:
        try:
            with open(fp) as f: doc = json.load(f)
        except Exception as ex:
            errors.append(f"{fp}: cannot parse JSON: {ex}"); continue
        check(doc, fp, errors)
        jsonschema_check(doc, fp, errors)
    if errors:
        print("INVALID:")
        for er in errors: print("  -", er)
        return 1
    print(f"OK: {len(files)} scorecard(s) valid against schema v1.0")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
