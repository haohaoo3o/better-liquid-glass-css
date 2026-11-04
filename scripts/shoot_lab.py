"""Render the parameter lab grid for review.

Output: docs/lab.png  (3200x1960, 2x)
"""
from __future__ import annotations

import sys

import http.server
import socketserver
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PORT = 8917
QUERY = sys.argv[1] if len(sys.argv) > 1 else ""
OUT = sys.argv[2] if len(sys.argv) > 2 else "lab.png"


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw)  # noqa: E731
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(1.0)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 980}, device_scale_factor=2)
        page.goto(f"http://127.0.0.1:{PORT}/demo/lab.html?{QUERY}", wait_until="networkidle")
        page.wait_for_function("window.__glassReady === true")
        page.wait_for_timeout(2200)
        page.screenshot(path=str(DOCS / OUT))
        browser.close()

    httpd.shutdown()
    from PIL import Image
    print(OUT, Image.open(DOCS / OUT).size)


if __name__ == "__main__":
    main()
