from playwright.sync_api import sync_playwright
from PIL import Image
import http.server, socketserver, threading, time
from pathlib import Path

ROOT = Path(r"D:/liquid-glass")
PORT = 8923
handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw)  # noqa: E731
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.8)

variants = {
    "A": "refr=210&bezel=0.22&chroma=1.05&mapScale=8&blur=0.8",
    "B": "refr=210&bezel=0.22&chroma=1.05&mapScale=8&blur=1.3",
}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=3)
    for k, q in variants.items():
        pg.goto(f"http://127.0.0.1:{PORT}/demo/optics.html?{q}", wait_until="networkidle")
        pg.wait_for_function("window.__glassReady === true")
        pg.wait_for_timeout(1600)
        pg.screenshot(path=str(ROOT / f"docs/_v{k}.png"), clip={"x": 1100, "y": 330, "width": 300, "height": 240})
    b.close()
httpd.shutdown()

for k in variants:
    im = Image.open(ROOT / f"docs/_v{k}.png").convert("RGB")
    print(k, im.size)
