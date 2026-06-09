#!/usr/bin/env python3
"""DOE Proof - Live: a local interactive UI over the REAL gate harness.

Pure stdlib (no deps). Run:  python3 serve.py [port]   then open the URL.

Honesty: every result comes from invoking the actual kit gate scripts via the
harness in run.py. The browser is a thin client -- all gate logic runs in Python
here. Nothing is simulated in JavaScript.
"""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROOF = Path(__file__).resolve().parent
sys.path.insert(0, str(PROOF))
import run as harness  # the real harness (invokes the real gates)

INDEX = PROOF / "live" / "index.html"


def _payload_preview(r):
    if r["method"] == "hook":
        return "".join(r["value_parts"])
    return (r.get("inject", "") or "").strip()


def _rows(results):
    out = []
    for r in results:
        out.append({
            "id": r["id"], "defectClass": r["class"],
            "gate": r["gate"] or "(no gate)",
            "enforcement": harness.ENFORCEMENT.get(r.get("expect"), "none"),
            "caught": bool(r["caught"]),
            "detail": (r.get("detail") or "").strip(),
            "payload": _payload_preview(r),
        })
    return out


def run_payload():
    sc, results, cov_caught, cov_total = harness.run()
    return {
        "rate": sc["catchRate"]["rate"],
        "injected": sc["catchRate"]["injected"],
        "caught": sc["catchRate"]["caught"],
        "covered": {"caught": cov_caught, "total": cov_total},
        "falsePositives": sc["falsePositives"],
        "provenance": sc["provenance"],
        "rows": _rows(results),
    }


def ablate_payload(disabled):
    sc, results, _, _ = harness.run()
    rows, caught = [], 0
    for r in _rows(results):
        off = r["gate"] in disabled
        eff = r["caught"] and not off
        if eff:
            caught += 1
        rows.append({**r, "disabled": off, "effCaught": eff})
    n = len(rows)
    return {"rate": round(caught / n, 4) if n else 0.0, "caught": caught, "injected": n, "rows": rows}


def probe(kind, payload):
    payload = payload or ""
    if not payload.strip():
        return {"fired": False, "gate": None, "reason": "type something first"}
    if kind == "command":
        e = {"tool_name": "Bash", "tool_input": {"command": payload}}
        f1, r1 = harness._run_hook("block_dangerous_commands.py", e)
        f2, r2 = harness._run_hook("block_secrets_in_code.py", e)
        if f1:
            return {"fired": True, "gate": "block_dangerous_commands", "reason": r1}
        if f2:
            return {"fired": True, "gate": "block_secrets_in_code", "reason": r2}
        return {"fired": False, "gate": None, "reason": "no gate fired -- this command would be allowed"}
    if kind == "write":
        e = {"tool_name": "Write", "tool_input": {"file_path": "user_file.py", "content": payload}}
        f, r = harness._run_hook("block_secrets_in_code.py", e)
        return {"fired": bool(f), "gate": "block_secrets_in_code" if f else None,
                "reason": r if f else "no secret pattern matched -- this write would be allowed"}
    if kind == "code":
        f, r = harness._run_filescan("\n\n" + payload + "\n", None)
        return {"fired": bool(f), "gate": "health_check" if f else None,
                "reason": "flagged by health_check (advisory)" if f else "nothing flagged -- this code would pass the scan"}
    return {"fired": False, "gate": None, "reason": "unknown probe kind"}


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._send(200, INDEX.read_text(encoding="utf-8"), "text/html; charset=utf-8")
        elif path == "/api/run":
            self._send(200, json.dumps(run_payload()))
        else:
            self._send(404, "{}")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            body = {}
        if self.path == "/api/ablate":
            self._send(200, json.dumps(ablate_payload(set(body.get("disabled", [])))))
        elif self.path == "/api/probe":
            self._send(200, json.dumps(probe(body.get("kind"), body.get("payload", ""))))
        else:
            self._send(404, "{}")

    def log_message(self, *a):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"DOE Proof - Live on http://127.0.0.1:{port}  (Ctrl-C to stop)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
