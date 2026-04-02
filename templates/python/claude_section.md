## Framework: Python

### Directory Structure (framework-specific)
```
src/           # Application source code
routes/        # API route handlers
tests/         # Test files
```

### Commands
- Dev: `uvicorn src.main:app --reload` or `flask run`
- Test: `pytest`, `ruff check .`
- Lint: `ruff check . --fix`
