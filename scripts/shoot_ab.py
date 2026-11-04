"""A/B: current showcase (refr 210) vs the fringe regime (refr 80, chroma 1.0)."""
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
import http.server, socketserver, threading, time
from pathlib import Path

ROOT = Path(r"D:/liquid-glass")
DOCS = ROOT / "docs"
PORT = 8929
handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw)  # noqa: E731
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.8)

VARIANTS = [
    ("current · refr 210 · chroma 1.05", "refr=210&bezel=0.22&chroma=1.05&mapScale=8&blur=1.0"),
    ("fringe regime · refr 80 · chroma 1.0", "refr=80&bezel=0.25&chroma=1.0&mapScale=8&blur=0.3"),
]
CLIP = {"x": 110, "y": 320, "width": 360, "height": 280}

shots = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=3)
    for i, (label, q) in enumerate(VARIANTS):
        pg.goto(f"http://127.0.0.1:{PORT}/demo/optics.html?{q}", wait_until="networkidle")
        pg.wait_for_function("window.__glassReady === true")
        pg.wait_for_timeout(1500)
        path = DOCS / f"_ab_{i}.png"
        pg.screenshot(path=str(path), clip=CLIP)
        shots.append((label, path))
    b.close()
httpd.shutdown()

tw = 620
cells = []
for label, path in shots:
    im = Image.open(path).convert("RGB")
    r = tw / im.width
    cells.append((label, im.resize((tw, int(im.height * r)), Image.LANCZOS)))
    path.unlink(missing_ok=True)

pad = 10
h = cells[0][1].height
out = Image.new("RGB", (tw * 2 + pad * 3, h + 54), (10, 13, 16))
d = ImageDraw.Draw(out)
for i, (label, im) in enumerate(cells):
    x = pad + i * (tw + pad)
    d.text((x + 2, 10), label, fill=(210, 218, 226))
    out.paste(im, (x, 32))
out.save(DOCS / "ab-regime.png", optimize=True)
print("ab-regime", out.size)
