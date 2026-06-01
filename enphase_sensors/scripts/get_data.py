#!/usr/bin/env python3
"""Fetch meter readings from a local Enphase IQ Gateway (Envoy)."""

from __future__ import annotations

import json
import sys

import requests
import urllib3

ENVOY_URL = "https://envoy.local/ivp/meters/readings"
TOKEN = (
    "eyJraWQiOiI3ZDEwMDA1ZC03ODk5LTRkMGQtYmNiNC0yNDRmOThlZTE1NmIiLCJ0eXAiOiJKV1Qi"
    "LCJhbGciOiJFUzI1NiJ9.eyJhdWQiOiIxMjIyMTQwNDI1ODkiLCJpc3MiOiJFbnRyZXoiLCJlbnB"
    "oYXNlVXNlciI6Im93bmVyIiwiZXhwIjoxODA5NzMzODc1LCJpYXQiOjE3NzgxOTc4NzUsImp0aSI"
    "6IjI4NmNiMGExLWU3NzAtNGY2My1iYTVlLWU0ODEwNThmYTIxYiIsInVzZXJuYW1lIjoibWFyYUB"
    "ibHVlYml0LmNvbS5hdSJ9.0rKXjaqYMpUowj3OiABMix197UbOvQ18vpTvdPlu6noL_oJETmOyLv"
    "R-QKGEUDxtBUZkYzBdv16XGt_MDVpkEg"
)


def fetch_meter_readings(url: str = ENVOY_URL, token: str = TOKEN, timeout: int = 10):
    # The Envoy uses a self-signed certificate, so disable verification and warnings.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, verify=False, timeout=timeout)
    response.raise_for_status()
    return response.json()


def main() -> int:
    try:
        data = fetch_meter_readings()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
