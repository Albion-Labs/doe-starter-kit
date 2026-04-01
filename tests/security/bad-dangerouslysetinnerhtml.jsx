// DELIBERATELY VULNERABLE — test fixture for pre-commit hook validation
// This file should be BLOCKED by security hooks.

import React from "react";

function UserContent({ userInput }) {
  // XSS vulnerability: unsanitised user input rendered as raw HTML in React
  return <div dangerouslySetInnerHTML={{__html: userInput}} />;
}

export default UserContent;
