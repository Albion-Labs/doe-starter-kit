# DOE Proof Kit

**Deterministic proof that DOE's gates catch real defects — reproducible on any machine, in one command.**

Not a demo, not a testimonial: a benchmark. We inject a corpus of known defects,
run the *actual, unmodified* DOE gate scripts against them, and score how many are
caught. Same inputs → same scorecard, every time. If you run it and don't get our
number, that's a bug and we want to hear about it.

---

## Show me the result (30 seconds)

Open `sample/scorecard.html` in any browser — a single self-contained file you can
email or AirDrop. Or generate a fresh one:

```bash
cd proof
python3 run.py                       # writes out/scorecard.json
python3 render.py out/scorecard.json out/scorecard.html
```

Expected: **6/6 covered defect classes caught**, control **0/7**, headline **86%**.

## Recreate it yourself (2 minutes)

Pure Python 3. **No pip install, no network, no API key, no LLM in the scoring path.**

**If you already use DOE** (you have the kit):
```bash
cd proof
python3 run.py --self-test
```

**If you're a skeptic without DOE** — the kit ships the gates *and* the harness together:
```bash
git clone <doe-starter-kit repo>
cd doe-starter-kit/proof
python3 run.py --self-test
# -> SELF-TEST PASSED (every covered fault caught, control clean, scorecard valid)
```

Run it ten times — identical result (only the timestamp changes). That's the
"deterministic" in DOE, demonstrated, not asserted.

## Don't trust the harness? Audit it.

Everything is plain text and the gates are the real product, not stubs we wrote to pass:

```bash
cat corpus/manifest.json                              # the exact faults, human-readable
cat ../.claude/hooks/block_secrets_in_code.py         # a REAL gate — read the actual code
python3 schema/validate.py out/scorecard.json         # result conforms to the locked v1.0 contract
```

The scorecard's `provenance` block records the **sha256 of each gate script** and the
**kit commit** it ran against. So the number is pinned to specific, inspectable code —
clone at that commit, run, and you must get the same result.

## Adversarial — prove the gates are load-bearing, not theatre

1. **Add your own defect.** Drop a new fault into `corpus/manifest.json`, re-run, and
   see whether DOE catches it. (If it doesn't, that's an honest gap — file it.)
2. **Break a gate.** Temporarily edit one of the gate scripts to do nothing, re-run, and
   watch the catch-rate fall. That fall is the proof the gate was doing real work.
3. **Check the control.** It's 0/7 because vanilla tooling (raw Claude, Lovable, Replit)
   has none of these gates. Not a trick — the actual counterfactual.

## Why 86% and not 100%?

One planted defect (`F07`) is a behavioural logic bug that **no static gate can catch** —
it needs a test or a human. We show it as an honest miss so you can see exactly where
DOE's gates stop. A benchmark that scores itself 100% is the one you shouldn't trust.

## What's in here

| Path | What |
|------|------|
| `schema/` | The v1.0 data contract (`scorecard.schema.json`) + dependency-free validator |
| `corpus/manifest.json` | The labelled fault corpus (trigger strings stored split so writing the file can't trip the gates under test) |
| `fixture/` | A synthetic, project-agnostic mini-project the file-scan gates run against |
| `run.py` | The harness — injects faults, invokes the real gates, scores, writes the scorecard |
| `render.py` | Scorecard JSON → self-contained HTML card |
| `sample/` | A reference scorecard (JSON + HTML) so you know what to expect |
| `SPEC.md` | Full design + the honest framing behind it |
