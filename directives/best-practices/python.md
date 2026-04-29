# Best Practices: Python

## Goal
Prevent common agent failure modes in Python before they reach commit.

## When to Use
Read before writing or modifying any Python file.

## Process

### Security
- Use `subprocess.run([...])` with a list of args (no `shell=True`, no `os.system()`) -- the list form passes args without shell parsing, eliminating command-injection vectors
- Build SQL queries with parameter bindings (`cursor.execute("... WHERE id = %s", (uid,))` or the ORM's parameterised API) -- f-strings and `.format()` interleave user input with the query, which is SQL injection
- Build shell commands with `subprocess.run([...])` and separate args -- f-strings into shell strings is command injection in waiting
- Import specific names (`from module import foo, bar`) -- explicit imports document dependencies and keep the namespace clean

### Correctness
- Default mutable arguments are a Python footgun: use `def f(items=None)` and assign `items = items or []` inside the function -- the default expression evaluates once at definition time, so a shared list/dict accumulates across calls
- Catch specific exception classes (`except FileNotFoundError`, `except json.JSONDecodeError`) -- bare `except:` and `except Exception:` swallow real errors and mask bugs
- Use `with` statements for file handles, DB connections, and locks -- the context manager guarantees cleanup even on exceptions
- Always specify `encoding='utf-8'` when opening text files — use `utf-8-sig` for files that may have BOM
- Always use `pathlib.Path` for file paths — never hardcoded string paths with `/` or `\\`
- Always guard script entry points with `if __name__ == '__main__':` — prevents side effects on import

### Maintainability
- Source paths, URLs, and credentials from config files, environment variables, or named module-level constants -- inline literals drift across edits and leak secrets into source
- When an error is intentionally non-fatal, log it (at minimum `logger.exception(...)`) before continuing -- silent `pass` in an except block hides the diagnostic
- Use `pathlib.Path` for path manipulation -- the `/` operator is platform-aware and the API is safer than string concatenation or `os.path.join()`
- Prefer list/dict/set comprehensions over manual loops for simple transforms

## Verification
- [ ] No bare `except:` blocks
- [ ] No mutable default arguments
- [ ] All file operations use `with` statements
- [ ] No `shell=True` in subprocess calls
- [ ] No hardcoded file paths (uses `Path` or config)
- [ ] `if __name__ == '__main__':` guard present where needed
