"""API smoke check for a local DevDocs AI stack.

Confirms health, database, session auth, and the unauthenticated / not-connected
gates. Does not call GitHub or OpenAI.

Usage (from the repo root, with the API already running):

    python scripts/smoke.py
    python scripts/smoke.py --base http://localhost:8001
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import sys
import urllib.error
import urllib.request
import uuid


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check a local DevDocs API")
    parser.add_argument("--base", default="http://localhost:8001")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            base + path,
            data=data,
            method=method,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        try:
            with opener.open(request, timeout=10) as response:
                raw = response.read()
                payload = json.loads(raw) if raw else None
                return response.status, payload
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                payload = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                payload = raw.decode("utf-8", errors="replace")
            return exc.code, payload
        except urllib.error.URLError as exc:
            print(f"FAIL {method} {path}: cannot reach {base} ({exc.reason})")
            print("Start Postgres and the API first. See README.md.")
            return 0, None

    def expect(
        method: str,
        path: str,
        http_status: int,
        body: dict | None = None,
        **checks: object,
    ) -> bool:
        code, payload = call(method, path, body)
        if code == 0:
            return False
        if code != http_status or not isinstance(payload, dict):
            print(f"FAIL {method} {path}: expected {http_status}, got {code} {payload}")
            return False
        for key, value in checks.items():
            if payload.get(key) != value:
                print(f"FAIL {method} {path}: {key}={payload.get(key)!r}, expected {value!r}")
                print(f"     body: {payload}")
                return False
        print(f"ok   {method} {path} -> {http_status}")
        return True

    email = f"smoke-{uuid.uuid4().hex[:12]}@example.com"
    password = "password123"
    steps = [
        expect("GET", "/health", 200, status="ok"),
        expect("GET", "/db/ping", 200, database="ok"),
        expect("GET", "/db/schema", 200, users_and_sessions=True),
        expect("POST", "/ask", 401, {"question": "ping"}, detail="Not authenticated"),
        expect("GET", "/github/repos", 401, detail="Not authenticated"),
        expect("POST", "/auth/register", 201, {"email": email, "password": password}, email=email),
        expect("POST", "/auth/login", 200, {"email": email, "password": password}, email=email),
        expect("GET", "/auth/me", 200, email=email),
        expect("GET", "/github/selected-repo", 200, selected=None),
        expect(
            "GET",
            "/github/repos",
            400,
            detail="GitHub is not connected. Connect GitHub first.",
        ),
        expect(
            "POST",
            "/ask",
            400,
            {"question": "What does this repository do?"},
            detail="No repository selected. Select a repository first.",
        ),
        expect("POST", "/auth/logout", 200, message="Logged out"),
        expect("GET", "/auth/me", 401, detail="Not authenticated"),
    ]
    if not all(steps):
        return 1
    print("smoke ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
