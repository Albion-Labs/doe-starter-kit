// DELIBERATELY VULNERABLE — test fixture for pre-commit hook validation
// This file should be BLOCKED by security hooks.

function renderUserComment(userInput) {
  const commentDiv = document.getElementById("comments");
  // XSS vulnerability: unsanitised user input injected as HTML
  commentDiv.innerHTML = userInput;
}
