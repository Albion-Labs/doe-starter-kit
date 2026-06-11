Open the HQ dashboard — a unified view of all your projects and their session histories.

## Steps

1. Determine the theme based on current time:
```bash
HOUR=$(date +%H)
if [ "$HOUR" -ge 6 ] && [ "$HOUR" -lt 18 ]; then
  THEME="light"
else
  THEME="dark"
fi
```

2. Run the HQ generator:
```bash
python3 ~/.claude/scripts/build_hq.py --theme $THEME --output ~/.claude/docs/hq.html
```

3. Open in browser:
```bash
open ~/.claude/docs/hq.html
```

4. Print a one-line summary: `HQ opened in browser. [N] projects, [S] total sessions.`

## Rules

- This is READ-ONLY. Does not modify any project files or the registry.
- Reads ~/.claude/project-registry.json to find registered projects.
- Projects are registered automatically by /wrap. No manual setup needed.
- If no projects are registered, report the error and suggest running /wrap in a project first.
- If a registered project path no longer exists, it is skipped gracefully.
- To remove a project from HQ, ask Claude to remove it from ~/.claude/project-registry.json.
- To rename a project's display name, ask Claude to set the displayName field in the registry.
