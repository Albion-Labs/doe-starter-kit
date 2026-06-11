"""Hook: Auto-copy plans written to ~/.claude/plans/ into the project's .claude/plans/ directory."""
import json, shutil, sys
from pathlib import Path

PROJECT_PLANS = Path(__file__).resolve().parent.parent / "plans"

def main():
    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    path = tool_input.get("file_path", "") or tool_input.get("path", "")

    home_plans = str(Path.home() / ".claude" / "plans")
    # v1.71.2: tool names are capitalised in real events ("Write"/"Edit"/
    # "MultiEdit") -- the original lowercase comparison meant this hook never
    # fired since it shipped (same casing class as the v1.59.0 matcher fix).
    if tool_name in ("Write", "Edit", "MultiEdit") and path.startswith(home_plans) and path.endswith(".md"):
        src = Path(path)
        if src.exists():
            PROJECT_PLANS.mkdir(parents=True, exist_ok=True)
            dest = PROJECT_PLANS / src.name
            shutil.copy2(str(src), str(dest))
            print(f"Auto-copied plan to project: .claude/plans/{src.name}")
    sys.exit(0)

if __name__ == "__main__":
    main()
