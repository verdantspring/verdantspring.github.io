import asyncio, os
from playwright.async_api import async_playwright
BASE="file://"+os.path.abspath("site")
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # archive scrolled to year list
        pg=await b.new_page(viewport={"width":1440,"height":960},device_scale_factor=2)
        await pg.goto(f"{BASE}/archive.html"); await pg.wait_for_timeout(800)
        await pg.evaluate("window.scrollTo(0,1400)"); await pg.wait_for_timeout(500)
        await pg.screenshot(path="build_src/shots/archive-rows.png")
        # a non-translated poem
        await pg.goto(f"{BASE}/p/71-north-nevada.html"); await pg.wait_for_timeout(900)
        await pg.screenshot(path="build_src/shots/poem-71.png")
        await b.close()
asyncio.run(main()); print("ok")
