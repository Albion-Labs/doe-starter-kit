Generate the global portfolio archive across all registered projects and open it in the browser. This is a read-only visualization command.

## Steps

1. Run the global archive generator:
```bash
python3 ~/.claude/scripts/build_global_archive.py --output ~/.claude/docs/global-archive.html
```

2. Open in browser:
```bash
open ~/.claude/docs/global-archive.html
```

3. Print a one-line summary: `Global archive opened in browser. [N] projects, [S] total sessions.`

## Rules

- This is READ-ONLY. Does not modify any project files.
- Reads ~/.claude/project-registry.json to find registered projects.
- If no projects are registered, report the error and suggest running /archive in a project first.
- If a registered project path no longer exists, it is skipped gracefully.
