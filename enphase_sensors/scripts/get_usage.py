#!/usr/bin/env python3
"""Fetch meter readings from a local Enphase IQ Gateway (Envoy)."""

from __future__ import annotations

import sys

import requests
import urllib3
import yaml


with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

envoy_host = config['envoy']['host']
ENVOY_URL = f"https://{envoy_host}/ivp/meters"
TOKEN = config['token']['access_token']


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

    # Solar Production
    production_power = data[0].get("activePower")
    production_voltage = data[0].get("voltage")
    production_current = data[0].get("current")
    production_freq = data[0].get("freq")

    # Grid Consumption
    net_consumption_power = data[1].get("activePower")
    net_consumption_voltage = data[1].get("voltage")
    net_consumption_current = data[1].get("current")
    net_consumption_freq = data[1].get("freq")

    # calculated import export values
    power_consumption = max(0, production_power + net_consumption_power)
    power_export = max(0, production_power - power_consumption)
    power_import = max(0, power_consumption - production_power)

    print(f"Production        : {production_power} W\t{production_voltage} V\t{production_current} A\t{production_freq} Hz")
    print(f"NetConsumption    : {net_consumption_power} W\t{net_consumption_voltage} V\t{net_consumption_current} A\t{net_consumption_freq} Hz")

    print(f"Power Used        : {power_consumption} W")
    print(f"Power Export      : {power_export} W")
    print(f"Power Import      : {power_import} W")

    #print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
