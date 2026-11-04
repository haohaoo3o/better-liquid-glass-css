"""Render a gradual ladder of refraction settings on the optics page.

Baseline = the settings already published in docs/optics.png
(refraction 170 / bezel 0.10 / chroma 0.95). Each step adds a little bend.

Output: docs/ladder.png
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
PORT = 8919
SCALE = 3
CLIP = {"x": 120, "y": 320, "width": 430, "height": 250}

STEPS = [
    ("baseline · refr 170 · bezel 0.10 · chroma 0.95", 170, 0.10, 0.95),
    ("+1 · refr 190 · bezel 0.16 · chroma 1.00", 190, 0.16, 1.00),
    ("+2 · refr 210 · bezel 0.22 · chroma 1.05", 210, 0.22, 1.05),
    ("+3 · refr 230 · bezel 0.30 · chroma 1.10", 230, 0.30, 1.10),
]


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw)  # noqa: E731
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(1.0)

    shots = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=SCALE)
        for i, (label, refr, bezel, chroma) in enumerate(STEPS):
            url = (f"http://127.0.0.1:{PORT}/demo/optics.html"
                   f"?refr={refr}&bezel={bezel}&chroma={chroma}&mapScale=5")
            page.goto(url, wait_until="networkidle")
            page.wait_for_function("window.__glassReady === true")
            page.wait_for_timeout(1600)
            path = DOCS / f"_ladder_{i}.png"
            page.screenshot(path=str(path), clip=CLIP)
            shots.append((label, path))
        browser.close()
    httpd.shutdown()

    target_w = 660
    rows = []
    for label, path in shots:
        im = Image.open(path).convert("RGB")
        ratio = target_w / im.width
        rows.append((label, im.resize((target_w, int(im.height * ratio)), Image.LANCZOS)))
        path.unlink(missing_ok=True)

    pad, gap = 10, 26
    total_h = sum(r.height + gap for _, r in rows) + pad
    out = Image.new("RGB", (target_w + pad * 2, total_h), (10, 13, 16))
    d = ImageDraw.Draw(out)
    y = pad
    for label, im in rows:
        d.text((pad + 2, y), label, fill=(200, 210, 220))
        y += 18
        out.paste(im, (pad, y))
        y += im.height + gap - 18

    out.save(DOCS / "ladder.png", optimize=True)
    print("ladder", out.size)


if __name__ == "__main__":
    main()
