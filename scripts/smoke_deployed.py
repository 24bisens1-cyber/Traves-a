#!/usr/bin/env python3
"""Live smoke check for a deployed TRAVESÍA URL (requires outbound network access)."""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


def get_json(base: str, path: str, timeout: int = 12):
    req = Request(urljoin(base, path), headers={"Accept":"application/json", "User-Agent":"TRAVESÍA-Deployment-Smoke/1.0"})
    with urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"{path} returned HTTP {response.status}")
        return json.loads(response.read(2_000_000).decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Deployed HTTPS URL, e.g. https://citypulsex.example.com")
    args = parser.parse_args()
    base = args.base_url.strip().rstrip("/") + "/"
    if not base.startswith("https://"):
        print("Refusing to test a non-HTTPS deployment URL.", file=sys.stderr)
        return 2
    results = []
    failures = []
    warnings = []
    def record(name, passed, detail=""):
        results.append({"check":name,"pass":bool(passed),"detail":detail})
        if not passed:
            failures.append(name)
    try:
        req = Request(urljoin(base, "/"), headers={"User-Agent":"TRAVESÍA-Deployment-Smoke/1.0"})
        with urlopen(req, timeout=12) as response:
            shell = response.read(2_000_000).decode("utf-8", errors="replace")
            record("Homepage returns HTTP 200 and TRAVESÍA shell", response.status == 200 and "TRAVESÍA" in shell, f"HTTP {response.status}")
        health = get_json(base, "/api/health")
        record("Health and configured database ready", health.get("status") == "ok" and health.get("database") == "ok", json.dumps({"status":health.get("status"),"database":health.get("database")}))
        capabilities = get_json(base, "/api/capabilities")
        record("Required TRAVESÍA capabilities reported", all(x in capabilities.get("modules",[]) for x in ("trip_pulseboard","expense_split","world_explorer")))
        provider_status = get_json(base, "/api/providers/status")
        record("Provider readiness endpoint returns a contract", bool(provider_status.get("providers")), f"{len(provider_status.get('providers',[]))} provider rows")
        maps = get_json(base, "/api/maps/config")
        nasa = next((x for x in maps.get("layers",[]) if x.get("id")=="nasa_gibs"), None)
        record("Public NASA imagery source is configured with attribution", bool(nasa and nasa.get("tile_url") and nasa.get("attribution") and maps.get("imagery_date")), str(maps.get("imagery_date")))
        # Actually request a sample tile from the configured remote imagery service.
        if nasa:
            tile = nasa["tile_url"].replace("{z}","2").replace("{y}","1").replace("{x}","2")
            try:
                tile_req = Request(tile, headers={"User-Agent":"TRAVESÍA-Deployment-Smoke/1.0"})
                with urlopen(tile_req, timeout=15) as response:
                    tile_type = response.headers.get("Content-Type", "")
                    record("NASA satellite tile is reachable over HTTPS", response.status == 200 and ("image" in tile_type or "octet-stream" in tile_type), f"HTTP {response.status}; {tile_type}")
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                record("NASA satellite tile is reachable over HTTPS", False, type(exc).__name__)
        # Weather should return real/provider-cached output, or explicitly fail closed if no valid contact is configured.
        weather_path = "/api/travel/weather?" + urlencode({"latitude":"21.1458","longitude":"79.0882","forecast_days":"3"})
        try:
            weather = get_json(base, weather_path)
            record("Weather endpoint returns a source-labelled provider response", bool(weather.get("source") and weather.get("data_mode") and weather.get("retrieved_at")), f"{weather.get('source')} · {weather.get('data_mode')}")
        except HTTPError as exc:
            body = exc.read(1_000_000).decode("utf-8", errors="replace")
            try: problem = json.loads(body)
            except ValueError: problem = {}
            record("Weather endpoint returns a source-labelled provider response", False, f"HTTP {exc.code}; {problem.get('data_mode','no data mode')} — set a valid CITYPULSEX_CONTACT_URL or email, then inspect provider/network terms")
        # Flight offers may intentionally be unconfigured; the hand-offs must exist instead of fake fare data.
        departure = datetime.now(timezone.utc).date().isoformat()
        from urllib.parse import urlparse
        payload = json.dumps({"origin":"NAG","destination":"GOI","departure_date":departure,"adults":1}).encode()
        flight_req = Request(urljoin(base, "/api/travel/flights/offers"), data=payload, headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"TRAVESÍA-Deployment-Smoke/1.0"}, method="POST")
        try:
            with urlopen(flight_req, timeout=18) as response:
                flight = json.loads(response.read(2_000_000).decode())
            record("Flight endpoint returns offers or honest search hand-offs", bool(flight.get("offers") or flight.get("alternatives")), f"HTTP 200; {flight.get('data_mode')}")
        except HTTPError as exc:
            body = exc.read(1_000_000).decode("utf-8", errors="replace")
            try: flight = json.loads(body)
            except ValueError: flight = {}
            record("Flight endpoint returns offers or honest search hand-offs", exc.code in (502,503) and len(flight.get("alternatives",[])) >= 2, f"HTTP {exc.code}; {flight.get('data_mode')}")
        for path in ("/pulseboard.js","/pulseboard.css","/world-game.js","/providers.js","/glb-viewer.js","/assets/companions3d/sprout.glb"):
            try:
                req = Request(urljoin(base,path), headers={"User-Agent":"TRAVESÍA-Deployment-Smoke/1.0"})
                with urlopen(req, timeout=12) as response:
                    record(f"Critical app asset serves: {path}", response.status == 200, f"HTTP {response.status}")
            except (HTTPError,URLError,TimeoutError,OSError) as exc:
                record(f"Critical app asset serves: {path}", False, type(exc).__name__)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        record("Deployment smoke workflow completed", False, f"{type(exc).__name__}: {exc}")
    print(json.dumps({"base_url":base,"passed":sum(x["pass"] for x in results),"total":len(results),"failed":failures,"warnings":warnings,"results":results},indent=2))
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
