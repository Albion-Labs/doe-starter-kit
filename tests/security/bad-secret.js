// DELIBERATELY VULNERABLE — test fixture for pre-commit hook validation
// This file should be BLOCKED by security hooks.

// Hardcoded secret: API keys must never appear in source code
const key = "sk_test_abcdefghijklmnopqrstuvwxyz123456";

function callApi(endpoint) {
  return fetch(endpoint, {
    headers: { Authorization: "Bearer " + key },
  });
}
