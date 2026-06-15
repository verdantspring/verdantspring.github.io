import asyncio, os
from playwright.async_api import async_playwright
BASE="file://"+os.path.abspath("site")
shots=[("index.html","cover","day"),("index.html","cover","night"),
       ("archive.html","archive","day"),
       ("p/bai-ca-duong-lieu.html","poem","day"),
       ("p/bai-ca-duong-lieu.html","poem","night")]
async def main():
    os.makedirs("build_src/shots",exist_ok=True)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for path,name,theme in shots:
            pg=await b.new_page(viewport={"width":1440,"height":960},device_scale_factor=2)
            await pg.goto(f"{BASE}/{path}")
            await pg.evaluate(f"document.documentElement.setAttribute('data-theme','{theme}')")
            await pg.wait_for_timeout(1400)
            await pg.screenshot(path=f"build_src/shots/{name}-{theme}.png")
            await pg.close()
        await b.close()
asyncio.run(main())
print("done")
