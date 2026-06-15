import asyncio, os
from playwright.async_api import async_playwright
BASE="file://"+os.path.abspath("site")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await b.new_page(viewport={"width":1440,"height":960},device_scale_factor=2)
        # a codex-translated poem (bilingual)
        await pg.goto(f"{BASE}/p/nu-hon-sao-bang.html"); await pg.wait_for_timeout(900)
        await pg.screenshot(path="build_src/shots/codex-poem.png")
        # archive top (now dense with EN badges)
        await pg.goto(f"{BASE}/archive.html"); await pg.wait_for_timeout(800)
        await pg.evaluate("window.scrollTo(0,1750)"); await pg.wait_for_timeout(400)
        await pg.screenshot(path="build_src/shots/archive-en.png")
        await b.close()
asyncio.run(main()); print("shot ok")
