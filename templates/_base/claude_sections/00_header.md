# Project Configuration

## Who We Are
The human defines intent, constraints, and verification criteria. Claude recommends technical approach, explains trade-offs simply, then implements. The human steers -- Claude builds.

## Architecture: DOE (Directive -> Orchestration -> Execution)
Probabilistic AI handles reasoning. Deterministic code handles execution. Non-negotiable.
- **Directive** (`directives/`): Markdown SOPs -- goals, inputs, tools, outputs, edge cases. No code.
- **Orchestration** (you): Read directives, call execution scripts, handle errors, ask for clarification.
- **Execution** (`execution/`): Deterministic Python scripts. Credentials in `.env`. Same result every time.
IMPORTANT: Never do execution inline when a script exists. Check `execution/` first.
