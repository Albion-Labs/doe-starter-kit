#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Security hook test runner
#
# Tests that pre-commit hooks correctly BLOCK known-bad patterns
# and ALLOW known-safe patterns (no false positives).
#
# Usage: ./run-security-tests.sh
# Exit:  0 if all tests pass, 1 if any test fails
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PASS=0
FAIL=0
TOTAL=0

# Colours (disable if not a terminal)
if [ -t 1 ]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[0;33m'
  NC='\033[0m'
else
  GREEN='' RED='' YELLOW='' NC=''
fi

# ── Helpers ──────────────────────────────────────────────────

assert_blocked() {
  local file="$1"
  local label="$2"
  TOTAL=$((TOTAL + 1))

  # Stage the file
  git -C "$REPO_ROOT" add "$file" 2>/dev/null

  # Attempt a dry-run commit — the pre-commit hook should reject it
  if git -C "$REPO_ROOT" commit --dry-run -m "test: security fixture" "$file" >/dev/null 2>&1; then
    # Hook did NOT block — test fails
    printf "${RED}FAIL${NC}  BLOCKED  %-45s  hook did not catch it\n" "$label"
    FAIL=$((FAIL + 1))
  else
    # Hook blocked the commit — expected
    printf "${GREEN}PASS${NC}  BLOCKED  %-45s  correctly rejected\n" "$label"
    PASS=$((PASS + 1))
  fi

  # Unstage so we leave the index clean
  git -C "$REPO_ROOT" reset HEAD -- "$file" >/dev/null 2>&1 || true
}

assert_allowed() {
  local file="$1"
  local label="$2"
  TOTAL=$((TOTAL + 1))

  # Stage the file
  git -C "$REPO_ROOT" add "$file" 2>/dev/null

  # Attempt a dry-run commit — should succeed (no false positive)
  if git -C "$REPO_ROOT" commit --dry-run -m "test: safe fixture" "$file" >/dev/null 2>&1; then
    printf "${GREEN}PASS${NC}  ALLOWED  %-45s  correctly permitted\n" "$label"
    PASS=$((PASS + 1))
  else
    printf "${RED}FAIL${NC}  ALLOWED  %-45s  false positive — hook blocked safe file\n" "$label"
    FAIL=$((FAIL + 1))
  fi

  # Unstage
  git -C "$REPO_ROOT" reset HEAD -- "$file" >/dev/null 2>&1 || true
}

# ── Test Cases ───────────────────────────────────────────────

echo ""
echo "Security Hook Tests"
echo "════════════════════════════════════════════════════════════"
echo ""

# Bad files — should be BLOCKED
assert_blocked "$SCRIPT_DIR/bad-innerhtml.js"              "innerHTML injection (JS)"
assert_blocked "$SCRIPT_DIR/bad-eval.js"                   "eval injection (JS)"
assert_blocked "$SCRIPT_DIR/bad-secret.js"                 "hardcoded API key"
assert_blocked "$SCRIPT_DIR/bad-shell.py"                  "subprocess shell=True (Python)"
assert_blocked "$SCRIPT_DIR/bad-dangerouslysetinnerhtml.jsx" "dangerouslySetInnerHTML (React)"

echo ""

# Good files — should be ALLOWED (no false positives)
assert_allowed "$SCRIPT_DIR/good-textcontent.js"           "textContent assignment (safe)"

# ── Summary ──────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════"
printf "Results: ${GREEN}%d passed${NC}, " "$PASS"
if [ "$FAIL" -gt 0 ]; then
  printf "${RED}%d failed${NC}" "$FAIL"
else
  printf "0 failed"
fi
printf " out of %d tests\n" "$TOTAL"
echo ""

if [ "$FAIL" -gt 0 ]; then
  printf "${YELLOW}Some security hooks are not catching expected patterns.${NC}\n"
  printf "Check .githooks/pre-commit and .claude/settings.json hook config.\n"
  echo ""
  exit 1
fi

exit 0
