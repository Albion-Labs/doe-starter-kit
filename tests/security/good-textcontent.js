// SAFE PATTERN — test fixture for false-positive validation
// This file should be ALLOWED by security hooks.

function renderUserComment(userInput) {
  const commentDiv = document.getElementById("comments");
  // Safe: textContent is not parsed as HTML, so no XSS risk
  commentDiv.textContent = userInput;
}

function updateTitle(title) {
  const heading = document.querySelector("h1");
  // Safe: textContent assignment
  heading.textContent = title;
}
