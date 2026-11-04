"""Render the optics test page (line pairs + glass) for the README.

Output: docs/optics.png  — with / without the glass plate, same crop, native 3x detail.
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
PORT = 8913
SCALE = 3
CLIP = {"x": 110, "y": 330, "width": 330, "height": 250}


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
        page.goto(f"http://127.0.0.1:{PORT}/demo/optics.html", wait_until="networkidle")
        page.wait_for_function("window.__glassReady === true")
        page.wait_for_timeout(1600)

        page.screenshot(path=str(DOCS / "optics_full.png"))
        page.screenshot(path=str(DOCS / "_optics_on.png"), clip=CLIP)
        page.evaluate("() => document.querySelectorAll('.lg-plate').forEach(e => e.style.display = 'none')")
        page.wait_for_timeout(400)
        page.screenshot(path=str(DOCS / "_optics_off.png"), clip=CLIP)
        browser.close()

    httpd.shutdown()

    on = Image.open(DOCS / "_optics_on.png").convert("RGB")
    off = Image.open(DOCS / "_optics_off.png").convert("RGB")
    target_w = 620
    ratio = target_w / on.width
    on_s = on.resize((target_w, int(on.height * ratio)), Image.LANCZOS)
    off_s = off.resize((target_w, int(off.height * ratio)), Image.LANCZOS)
    gap = 16
    out = Image.new("RGB", (target_w * 2 + gap, on_s.height + 78), (10, 13, 16))
    out.paste(off_s, (0, 62))
    out.paste(on_s, (target_w + gap, 62))
    d = ImageDraw.Draw(out)
    d.text((4, 22), "line pairs, no glass", fill=(150, 160, 170))
    d.text((target_w + gap + 4, 22), "line pairs behind the glass rim", fill=(210, 218, 226))
    out.save(DOCS / "optics.png", optimize=True)

    # 1:1 native crop, upscaled 2x so the fringe is readable in the README.
    tight = on.crop((0, 0, min(on.width, 900), min(on.height, 700)))
    tight = tight.resize((tight.width * 2, tight.height * 2), Image.LANCZOS)
    tight.save(DOCS / "dispersion.png", optimize=True)
    (DOCS / "_optics_on.png").unlink(missing_ok=True)
    (DOCS / "_optics_off.png").unlink(missing_ok=True)
    print("optics", out.size)


if __name__ == "__main__":
    main()
