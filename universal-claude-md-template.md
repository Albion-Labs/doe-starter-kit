# Universal Learnings

Cross-project patterns that apply to any codebase. Auto-loaded by Claude Code at every session start.

<!-- 
Claude: short bullet points under descriptive ## headings. One learning per line.
Max 30 lines of content. When full, remove the least useful before adding new.
Only truly universal patterns here — project-specific learnings go in that project's learnings.md.
Tag source: e.g. "[retro: feature-name vX.Y.Z]"

## Python Execution

- When caching large API downloads to disk, always delete stale caches before re-running with different parameters (e.g. changed page size). A partial cache from a previous run will silently produce incomplete results. [retro: universal]
- macOS system Python 3.9 has an old OpenSSL that fails TLS 1.3 sites (`TLSV1_ALERT_PROTOCOL_VERSION`). Use `subprocess` + `curl` for downloads from sites requiring modern TLS. [retro: universal]

## Shell & Platform

- macOS `sed -i` requires an empty backup extension: `sed -i '' '...'`. Linux uses `sed -i '...'` with no argument. Git hooks and shell scripts must account for this or they'll fail silently on one platform. [retro: universal]

## Verification

- After creating or editing files, verify with `ls`/`cat`/`grep` before reporting success. Don't skip this even for "obvious" edits. [retro: universal]
-->
