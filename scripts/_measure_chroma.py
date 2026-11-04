"""Measure actual R/G/B edge separation across the glass rim.

Renders optics.html at two chroma values, takes a horizontal scanline through the
lens, finds the strongest gradient per channel, and prints the offsets in pixels.
"""
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np, http.server, socketserver, threading, time
from pathlib import Path

ROOT = Path(r"D:/liquid-glass")
PORT = 8925
handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw)  # noqa: E731
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.8)

CASES = {
    "chroma 0": "refr=210&bezel=0.22&chroma=0&mapScale=8&blur=0",
    "chroma 1.05": "refr=210&bezel=0.22&chroma=1.05&mapScale=8&blur=0",
    "chroma 2.5": "refr=210&bezel=0.22&chroma=2.5&mapScale=8&blur=0",
}

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1)
    for name, q in CASES.items():
        pg.goto(f"http://127.0.0.1:{PORT}/demo/optics.html?{q}", wait_until="networkidle")
        pg.wait_for_function("window.__glassReady === true")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=str(ROOT / f"docs/_scan_{name.split()[1]}.png"))
    b.close()
httpd.shutdown()


def edges(path: str, y: int, x0: int, x1: int):
    im = np.asarray(Image.open(path).convert("RGB")).astype(float)
    out = {}
    for i, ch in enumerate("RGB"):
        row = im[y, x0:x1, i]
        g = np.abs(np.diff(row))
        out[ch] = int(np.argmax(g)) + x0
    return out


for name in CASES:
    f = ROOT / f"docs/_scan_{name.split()[1]}.png"
    # scanline just above the pill's vertical centre, inside the left cap
    for y in (420, 450):
        e = edges(str(f), y, 150, 420)
        print(f"{name:12s} y={y} R={e['R']} G={e['G']} B={e['B']}  "
              f"R-B spread = {abs(e['R'] - e['B'])} px")
