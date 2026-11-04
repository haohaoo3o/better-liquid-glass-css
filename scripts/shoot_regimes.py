"""Chroma regime test: small displacement + measurable channel split.

The fringe is visible when the per-channel offset is comparable to the feature size,
not when the whole scene is displaced by hundreds of pixels.
"""
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
import http.server, socketserver, threading, time
from pathlib import Path

ROOT = Path(r"D:/liquid-glass")
DOCS = ROOT / "docs"
PORT = 8927
handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw)  # noqa: E731
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.8)

ROWS = [
    ("refr 40 · chroma 0.5", 40, 0.50),
    ("refr 40 · chroma 1.0", 40, 1.00),
    ("refr 40 · chroma 1.5", 40, 1.50),
    ("refr 80 · chroma 0.5", 80, 0.50),
    ("refr 80 · chroma 1.0", 80, 1.00),
    ("refr 80 · chroma 1.5", 80, 1.50),
]
CLIP = {"x": 110, "y": 350, "width": 300, "height": 200}

shots = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=3)
    for i, (label, refr, chroma) in enumerate(ROWS):
        q = f"refr={refr}&bezel=0.25&chroma={chroma}&mapScale=8&blur=0.3"
        pg.goto(f"http://127.0.0.1:{PORT}/demo/optics.html?{q}", wait_until="networkidle")
        pg.wait_for_function("window.__glassReady === true")
        pg.wait_for_timeout(1500)
        path = DOCS / f"_cr_{i}.png"
        pg.screenshot(path=str(path), clip=CLIP)
        shots.append((label, path))
    b.close()
httpd.shutdown()

tw = 460
cells = []
for label, path in shots:
    im = Image.open(path).convert("RGB")
    r = tw / im.width
    cells.append((label, im.resize((tw, int(im.height * r)), Image.LANCZOS)))
    path.unlink(missing_ok=True)

pad = 8
cols = 3
cw, chh = cells[0][1].size
rows = (len(cells) + cols - 1) // cols
out = Image.new("RGB", (cw * cols + pad * (cols + 1), (chh + 30) * rows + pad), (10, 13, 16))
d = ImageDraw.Draw(out)
for i, (label, im) in enumerate(cells):
    c, r = i % cols, i // cols
    x = pad + c * (cw + pad)
    y = pad + r * (chh + 30)
    d.text((x + 2, y + 4), label, fill=(200, 210, 220))
    out.paste(im, (x, y + 24))

out.save(DOCS / "chroma-regimes.png", optimize=True)
print("chroma-regimes", out.size)
