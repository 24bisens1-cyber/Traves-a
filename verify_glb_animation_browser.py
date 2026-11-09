#!/usr/bin/env python3
"""Verify that every bundled rigged GLB loads and that animation visibly changes frames.

This uses Chromium + a self-contained canvas renderer, so verification doesn't need
WebGL drivers or a third-party CDN. Install Playwright and Chromium to run it.
"""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "frontend" / "assets" / "companions3d"
SLUGS = ("bloop", "mira", "orbit", "paws", "pip", "roo", "sprout")


def main() -> int:
    source = (ROOT / "frontend" / "glb-viewer.js").read_text(encoding="utf-8")
    checks: list[dict[str, object]] = []
    page_errors: list[str] = []
    def check(name: str, ok: bool, **details: object) -> None:
        checks.append({"name": name, "pass": bool(ok), **details})
    with sync_playwright() as p:
        opts: dict[str, object] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        executable = os.environ.get("CHROMIUM_EXECUTABLE", "/usr/bin/chromium")
        if Path(executable).exists():
            opts["executable_path"] = executable
        browser = p.chromium.launch(**opts)
        page = browser.new_page(viewport={"width": 920, "height": 780}, device_scale_factor=1)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.set_content('<!doctype html><meta charset="utf-8"><main style="width:450px;height:390px;margin:15px auto;background:#dcebe0;border-radius:22px"><div id="stage" style="width:100%;height:100%"></div></main><img id="portrait" hidden><p id="status"></p>')
        page.add_script_tag(content=source)
        page.add_script_tag(content=(ROOT / "frontend" / "companion-3d.js").read_text(encoding="utf-8"))
        for slug in SLUGS:
            encoded = base64.b64encode((ASSET_DIR / f"{slug}.glb").read_bytes()).decode("ascii")
            page.evaluate("""payload=>{const bytes=Uint8Array.from(atob(payload),c=>c.charCodeAt(0));window.fetch=async()=>new Response(bytes.buffer,{status:200});}""", encoded)
            page.evaluate("""slug=>{window.cityRig?.dispose();window.cityRig=window.CityPulse3DCompanions.mount(document.querySelector('#stage'),slug,document.querySelector('#portrait'),(msg,ok)=>{const s=document.querySelector('#status');s.textContent=msg;s.dataset.ok=String(ok);},{assetUrl:'/local-test.glb'});}""", slug)
            page.wait_for_function("document.querySelector('#status').dataset.ok==='true' && document.querySelector('#status').textContent.includes('self-contained renderer')", timeout=8000)
            check(f"{slug} GLB loads with 12 joints and 7 clips", "12 joints" in page.locator("#status").inner_text() and "7 clips" in page.locator("#status").inner_text(), status=page.locator("#status").inner_text())
            if slug == "bloop":
                base = page.locator("canvas").evaluate("e=>e.toDataURL()")
                has_look_at = page.evaluate("typeof window.cityRig.lookAt === 'function'")
                if has_look_at:
                    page.evaluate("window.cityRig.lookAt(1,0.8)")
                    looking = page.locator("canvas").evaluate("e=>e.toDataURL()")
                    check("Bloop head responds to pointer look direction", looking != base, frame_changed=looking != base)
                    page.evaluate("window.cityRig.lookAt(0,0)")
                    base = page.locator("canvas").evaluate("e=>e.toDataURL()")
                else:
                    check("Bloop head responds to pointer look direction", False)
                for action, label in (("hello", "Wave"), ("dance", "Dance"), ("hop", "AdventureHop"), ("walk", "Walk"), ("turn", "Turn"), ("point", "Point")):
                    page.evaluate("action=>window.cityRig.play(action)", action)
                    page.wait_for_timeout(240)
                    shot1 = page.locator("canvas").evaluate("e=>e.toDataURL()")
                    page.wait_for_timeout(240)
                    shot2 = page.locator("canvas").evaluate("e=>e.toDataURL()")
                    check(f"{label} animation renders moving frames", shot1 != base and shot2 != shot1, frame_a_changed=shot1 != base, frame_b_changed=shot2 != shot1)
                    base = page.locator("canvas").evaluate("e=>e.toDataURL()")
                screenshot_path = Path(os.environ.get("CITYPULSEX_GLB_SCREENSHOT", str(Path(tempfile.gettempdir()) / "TRAVESÍA_3D_Companion_Verified.png"))).expanduser().resolve()
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path), full_page=True)
            page.wait_for_timeout(80)
        browser.close()
    result = {"passed": sum(bool(c["pass"]) for c in checks), "total": len(checks), "checks": checks, "browser_errors": page_errors}
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] == result["total"] and not page_errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
