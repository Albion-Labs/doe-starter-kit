#!/usr/bin/env python3
"""Build a portable, self-contained DOE Proof Kit zip.

Packages the proof/ subsystem + the live UI + the REAL gate scripts it tests +
provenance, so anyone can run it with no access to the kit. Layout mirrors the
kit's relative paths so run.py/serve.py work unchanged.

Usage: python3 make_bundle.py   ->   out/doe-proof-kit.zip
"""
import hashlib, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

PROOF = Path(__file__).resolve().parent
KIT = PROOF.parent
OUT = PROOF / "out"
STAGE = OUT / "doe-proof-kit"
GATES = ["block_secrets_in_code.py", "block_dangerous_commands.py"]

def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

def main():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / ".claude" / "hooks").mkdir(parents=True)
    (STAGE / "execution").mkdir(parents=True)

    # proof subsystem (skip generated/dev cruft + the bundler itself)
    shutil.copytree(PROOF, STAGE / "proof",
                    ignore=shutil.ignore_patterns("out", ".tmp", "__pycache__", "*.pyc", "make_bundle.py"))
    # the REAL gates under test
    for g in GATES:
        shutil.copy2(KIT / ".claude" / "hooks" / g, STAGE / ".claude" / "hooks" / g)
    for f in ("health_check.py", "verify.py"):
        shutil.copy2(KIT / "execution" / f, STAGE / "execution" / f)

    commit = ""
    try:
        commit = subprocess.run(["git", "-C", str(KIT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        pass
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    prov = [f"DOE Proof Kit - portable bundle",
            f"built:      {stamp}",
            f"kit commit: {commit or 'UNKNOWN'}", "",
            "Bundled gate scripts (sha256, first 16) - these ARE the real shipped gates:"]
    for rel in [".claude/hooks/block_secrets_in_code.py",
                ".claude/hooks/block_dangerous_commands.py",
                "execution/health_check.py"]:
        prov.append(f"  {sha16(STAGE / rel)}  {rel}")
    (STAGE / "PROVENANCE.txt").write_text("\n".join(prov) + "\n")

    (STAGE / "verify.sh").write_text(
        '#!/usr/bin/env bash\ncd "$(dirname "$0")/proof" && exec python3 run.py --self-test\n')
    (STAGE / "live.sh").write_text(
        '#!/usr/bin/env bash\n'
        'PORT="${1:-8765}"\ncd "$(dirname "$0")/proof"\n'
        'echo "DOE Proof - Live on http://127.0.0.1:$PORT  (Ctrl-C to stop)"\n'
        '(command -v open >/dev/null && open "http://127.0.0.1:$PORT") '
        '|| (command -v xdg-open >/dev/null && xdg-open "http://127.0.0.1:$PORT") || true\n'
        'exec python3 serve.py "$PORT"\n')
    for s in ("verify.sh", "live.sh"):
        os.chmod(STAGE / s, 0o755)

    (STAGE / "README.txt").write_text(
        "DOE PROOF KIT - portable bundle\n"
        "================================\n\n"
        "A reproducible benchmark proving DOE's gates catch real defects. Pure Python 3,\n"
        "no install, no network. It ships the REAL gate scripts (see PROVENANCE.txt), so\n"
        "it tests the actual gates - not stubs.\n\n"
        "RUN IT (headless, deterministic):\n"
        "    python3 proof/run.py --self-test        (or:  bash verify.sh)\n"
        "    -> 6/6 covered classes caught, 0 measured false-positives, control 0/7.\n\n"
        "RUN IT (interactive, in your browser):\n"
        "    bash live.sh                            (opens http://127.0.0.1:8765)\n"
        "    Run it, disable a gate and watch the score fall, or type your own payload\n"
        "    in 'Beat the gates' and throw it at the real gate.\n\n"
        "AUDIT IT:\n"
        "    cat proof/corpus/manifest.json          the exact injected defects\n"
        "    cat .claude/hooks/block_secrets_in_code.py   a real gate (not a stub)\n"
        "    cat PROVENANCE.txt                       gate hashes + kit commit\n\n"
        "Full guide: proof/README.md\n")

    # self-verify the staged bundle actually runs standalone
    r = subprocess.run([sys.executable, "run.py", "--self-test"],
                       cwd=str(STAGE / "proof"), capture_output=True, text=True)
    if r.returncode != 0:
        print("BUNDLE SELF-TEST FAILED:\n" + r.stdout + r.stderr)
        return 1
    print("bundle self-test: PASS (runs standalone, gates resolve)")

    zip_path = shutil.make_archive(str(OUT / "doe-proof-kit"), "zip", root_dir=str(OUT), base_dir="doe-proof-kit")
    size = os.path.getsize(zip_path)
    nfiles = sum(len(f) for _, _, f in os.walk(STAGE))
    print(f"bundle -> {zip_path}  ({size//1024} KB, {nfiles} files)  kit {commit[:8]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
