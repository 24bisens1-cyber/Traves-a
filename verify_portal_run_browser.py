#!/usr/bin/env python3
"""Optional browser smoke test for Portal Run. Requires Playwright + Chromium.

Install with: python -m pip install playwright && playwright install chromium
Then run: python scripts/verify_portal_run_browser.py
Use --screenshot path.png to capture the rendered game panel.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", help="Optional path for a game-panel screenshot")
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed. Install it with: python -m pip install playwright", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[1]
    css = (root / "frontend" / "styles.css").read_text(encoding="utf-8")
    js = (root / "frontend" / "world-game.js").read_text(encoding="utf-8")
    html = (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>body{margin:0;background:#f7f5ef;font:14px Arial}'
        '.page{max-width:1200px;margin:0 auto;padding:24px}'
        '.hero-art{height:180px;background:#cfe0d6;position:relative;overflow:hidden}'
        '.globe-atmosphere{position:absolute;inset:0}.floating-note{position:absolute;left:10px;top:10px}'
        + css
        + '</style></head><body><div class="page"><div class="hero-art">'
        '<div class="globe-atmosphere"></div><div class="floating-note">Pointer-reactive hero</div>'
        '</div><div id="gameHost"></div></div>'
        '<script>window.__localStore={};Object.defineProperty(window,"localStorage",{configurable:true,value:{'
        'getItem:(k)=>window.__localStore[k]??null,setItem:(k,v)=>window.__localStore[k]=String(v),'
        'removeItem:(k)=>delete window.__localStore[k]}});</script>'
        '<script>' + js + '</script>'
        '<script>document.getElementById("gameHost").innerHTML=window.CityPulseWorldGame.markup();'
        'window.CityPulseWorldGame.init();</script></body></html>'
    )

    results: list[dict[str, object]] = []
    page_errors: list[str] = []
    with sync_playwright() as p:
        executable = os.environ.get("CHROMIUM_EXECUTABLE") or ("/usr/bin/chromium" if Path("/usr/bin/chromium").exists() else "")
        launch_options = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if executable and Path(executable).exists():
            launch_options["executable_path"] = executable
        browser = p.chromium.launch(**launch_options)
        page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.set_content(html, wait_until="load")
        page.wait_for_selector("#gameStage")
        stage = page.locator("#gameStage")

        def check(name: str, passed: bool, **detail: object) -> None:
            results.append({"name": name, "pass": bool(passed), **detail})

        check("game mounts and target begins disabled", page.locator("#worldGame").count() == 1 and page.locator("#gameTarget").is_disabled())
        box = stage.bounding_box()
        assert box is not None
        page.mouse.move(box["x"] + box["width"] * .8, box["y"] + box["height"] * .2)
        shift = stage.evaluate('(e)=>e.style.getPropertyValue("--shift-x")')
        check("cursor updates parallax variables", bool(shift and shift not in ("0px", "0")), value=shift)
        page.mouse.click(box["x"] + 8, box["y"] + 8)
        check("background click creates a pulse", page.locator(".game-ripple").count() >= 1)
        page.locator("#gameStart").click()
        check("launch starts timer and enables target", page.locator("#gameTarget").is_enabled() and stage.get_attribute("data-game-state") == "running")
        # The target is intentionally animated and relocates after each collection.
        # Invoke the real button click handler directly so the test does not depend on
        # a stale screen coordinate hitting a moving target.
        page.locator("#gameTarget").evaluate("el => { for (let i = 0; i < 7; i++) { if (!el.disabled) el.click(); } }")
        page.wait_for_timeout(50)
        score = page.locator("#gameScore").inner_text().strip()
        check("seven collections unlock the portal", score == "07" and page.locator("#gameWinOverlay").is_visible(), score=score)
        best = page.evaluate("window.__localStore['citypulsex.portal-run.best']")
        check("best score is recorded", best == "7", best=best)
        page.locator("#gameReset").click()
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(100)
        metrics = page.evaluate('() => ({pageWidth:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth})')
        check("mobile page fits the viewport", metrics["pageWidth"] <= metrics["viewport"] + 2, metrics=metrics)
        if args.screenshot:
            output = Path(args.screenshot).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            page.set_viewport_size({"width": 1440, "height": 1050})
            page.locator("#worldGame").scroll_into_view_if_needed()
            page.screenshot(path=str(output), full_page=False)
            print(f"Screenshot: {output}")
        browser.close()

    payload = {"checks": results, "passed": sum(bool(x["pass"]) for x in results), "total": len(results), "page_errors": page_errors}
    print(json.dumps(payload, indent=2))
    return 0 if payload["passed"] == payload["total"] and not page_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
