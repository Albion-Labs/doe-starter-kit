# Best Practices: Python

## Goal
Prevent common agent failure modes in Python before they reach commit.

## When to Use
Read before writing or modifying any Python file.

## Process

### Security
- Never use `os.system()` or `subprocess` with `shell=True` — use `subprocess.run()` with a list of args (command injection risk)
- Never use f-strings or `.format()` to build SQL queries — use parameterised queries
- Never use f-strings to build shell commands — use `subprocess.run([...])` with separate args
- Never use `import *` — import specific names (hides dependencies, pollutes namespace)

### Correctness
- Never use mutable default arguments (`def f(items=[])`) — use `None` and assign inside the function
- Always catch specific exceptions — never bare `except:` or `except Exception:` (swallows real errors)
- Always use `with` statements for file handles, DB connections, locks — never manual open/close
- Always specify `encoding='utf-8'` when opening text files — use `utf-8-sig` for files that may have BOM
- Always use `pathlib.Path` for file paths — never hardcoded string paths with `/` or `\\`
- Always guard script entry points with `if __name__ == '__main__':` — prevents side effects on import

### Maintainability
- Never hardcode file paths, URLs, or credentials — use config, environment variables, or constants
- Never silence errors with `pass` in except blocks — at minimum log the error
- Always use `Path` for path manipulation — never `os.path.join()` or string concatenation
- Prefer list/dict/set comprehensions over manual loops for simple transforms

## Verification
- [ ] No bare `except:` blocks
- [ ] No mutable default arguments
- [ ] All file operations use `with` statements
- [ ] No `shell=True` in subprocess calls
- [ ] No hardcoded file paths (uses `Path` or config)
- [ ] `if __name__ == '__main__':` guard present where needed
