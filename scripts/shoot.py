"""Render the demo page to README screenshots.

Usage:  python scripts/shoot.py
Output:
  docs/preview.png     2400x1350  full page
  docs/preview@3x.png  4800x2700  full page, native 3x
  docs/dispersion.png  1080x900   edge crop at native 3x
  docs/compare.png     with / without the glass plate, same crop
"""
from __future__ import annotations

import http.server
import socketserver
import threading
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PORT = 8909
SCALE = 3
CLIP = {"x": 60, "y": 176, "width": 360, "height": 300}


def serve() -> socketserver.TCPServer:
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw)  # noqa: E731
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    httpd = serve()
    time.sleep(1.0)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=SCALE)
        page.goto(f"http://127.0.0.1:{PORT}/demo/index.html", wait_until="networkidle")
        page.wait_for_function("window.__glassReady === true")
        page.wait_for_timeout(1800)

        page.screenshot(path=str(DOCS / "preview@3x.png"))
        page.screenshot(path=str(DOCS / "dispersion.png"), clip=CLIP)

        # Same crop with the plates switched off, for a side-by-side comparison.
        page.evaluate("() => document.querySelectorAll('.lg-plate').forEach(e => e.style.display = 'none')")
        page.wait_for_timeout(400)
        page.screenshot(path=str(DOCS / "_off.png"), clip=CLIP)
        browser.close()

    httpd.shutdown()

    full = Image.open(DOCS / "preview@3x.png").convert("RGB")
    full.resize((full.width // 2, full.height // 2), Image.LANCZOS).save(DOCS / "preview.png", optimize=True)

    on = Image.open(DOCS / "dispersion.png").convert("RGB")
    off = Image.open(DOCS / "_off.png").convert("RGB")
    target_w = 640
    ratio = target_w / on.width
    on_s = on.resize((target_w, int(on.height * ratio)), Image.LANCZOS)
    off_s = off.resize((target_w, int(off.height * ratio)), Image.LANCZOS)
    gap = 16
    compare = Image.new("RGB", (target_w * 2 + gap, on_s.height + 78), (10, 13, 16))
    compare.paste(off_s, (0, 62))
    compare.paste(on_s, (target_w + gap, 62))
    d = ImageDraw.Draw(compare)
    d.text((4, 22), "WITHOUT the glass plate", fill=(150, 160, 170))
    d.text((target_w + gap + 4, 22), "WITH the glass plate (refraction + dispersion)", fill=(210, 218, 226))
    compare.save(DOCS / "compare.png", optimize=True)
    (DOCS / "_off.png").unlink(missing_ok=True)

    print("preview   ", Image.open(DOCS / "preview.png").size)
    print("3x        ", full.size)
    print("dispersion", on.size)
    print("compare   ", compare.size)


if __name__ == "__main__":
    main()
