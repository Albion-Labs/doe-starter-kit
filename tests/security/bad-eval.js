// DELIBERATELY VULNERABLE — test fixture for pre-commit hook validation
// This file should be BLOCKED by security hooks.

function calculate(userInput) {
  // Code injection vulnerability: arbitrary code execution from user input
  const result = eval(userInput);
  return result;
}
