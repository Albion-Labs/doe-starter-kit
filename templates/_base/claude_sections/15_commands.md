## Common Commands
```bash
# Verify task contracts
python3 execution/verify.py

# Run DOE methodology health check
python3 execution/test_methodology.py

# Project health check (stubs, TODOs, empty functions)
python3 execution/health_check.py

# Quality gate (mid-feature checkpoint / pre-retro)
python3 execution/quality_gate.py --checkpoint
python3 execution/quality_gate.py --pre-retro

# Activate git hooks
git config core.hooksPath .githooks

# Create PR from feature branch
gh pr create --title "..." --body "..."
```
