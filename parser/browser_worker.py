"""
Standalone browser worker process.
Runs Playwright in its own process - completely avoids Windows asyncio issues.
Communicates via stdin/stdout JSON protocol.

On Windows, ProactorEventLoop IS required for subprocess (create_subprocess_exec).
That's fine here - this IS a subprocess, so ProactorEventLoop works perfectly.
We don't use sync_playwright greenlets, just pure asyncio + async_playwright.
"""
import sys
import json
import re
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = await browser.new_page()

        # Signal ready
        print(json.dumps({"status": "ready"}), flush=True)

        own_pattern = r"보험사고\s*이력\s*\(내차\s*피해\)\s*(\d+)회\s*([\d,]+)원"
        other_pattern = r"보험사고\s*이력\s*\(타차\s*가해\)\s*(\d+)회[/\s]*([\d,]+)원"

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                continue

            if req.get("cmd") == "quit":
                break

            url = req.get("url")
            vehicle_id = req.get("vehicle_id")

            try:
                await page.goto(url, wait_until="load", timeout=10000)
                await page.wait_for_selector("body", timeout=3000)
                page_text = await page.evaluate("() => document.body.innerText")

                has_accident = False
                details = []

                for match in re.findall(own_pattern, page_text):
                    count = int(match[0])
                    if count > 0:
                        has_accident = True
                        details.append({
                            "accident_type": "Accidents Caused By Other Drivers",
                            "accident_count": count,
                            "total_cost": match[1],
                        })

                for match in re.findall(other_pattern, page_text):
                    count = int(match[0])
                    if count > 0:
                        has_accident = True
                        details.append({
                            "accident_type": "Accidents Caused By This Car's Owner",
                            "accident_count": count,
                            "total_cost": match[1],
                        })

                print(json.dumps({
                    "vehicle_id": vehicle_id,
                    "has_accident": has_accident,
                    "details": details,
                }), flush=True)

            except Exception as e:
                print(json.dumps({
                    "vehicle_id": vehicle_id,
                    "error": str(e),
                    "has_accident": None,
                    "details": [],
                }), flush=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
