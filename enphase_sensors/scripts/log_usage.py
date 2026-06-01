#!/usr/bin/env python3
"""Fetch meter readings from a local Enphase IQ Gateway (Envoy)."""

from __future__ import annotations

from datetime import datetime
import time
import json
import sys

import requests
import urllib3
import yaml


class LastRunData:
    def __init__(self):
        self.last_run_time = None
        self.last_production_actEnergyDlvd = 0
        self.last_production_actEnergyRcvd = 0
        self.last_net_consumption_actEnergyDlvd = 0
        self.last_net_consumption_actEnergyRcvd = 0


def load_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config


def get_token(config):
    access_token = config['token']['access_token']
    return access_token


def fetch_meter_readings(config, timeout: int = 10):
    # The Envoy uses a self-signed certificate, so disable verification and warnings.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    envoy_host = config['envoy']['host']
    envoy_url = f"https://{envoy_host}/ivp/meters/readings"
    access_token = get_token(config)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    response = requests.get(envoy_url, headers=headers, verify=False, timeout=timeout)
    response.raise_for_status()
    return response.json()


def main(config, last_run_data: LastRunData, verbose: bool = False) -> int:
    try:
        data = fetch_meter_readings(config)
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    # samples timestamp
    timestamp_epoc = data[0].get("timestamp")
    data_timestamp = datetime.fromtimestamp(timestamp_epoc)
    timestamp_str = data_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')

    # Solar Production
    production_actEnergyDlvd = data[0].get("actEnergyDlvd")
    production_actEnergyRcvd = data[0].get("actEnergyRcvd")
    production_power = data[0].get("activePower")
    production_voltage = data[0].get("voltage")
    production_current = data[0].get("current")
    production_freq = data[0].get("freq")

    # Grid Consumption
    net_consumption_actEnergyDlvd = data[1].get("actEnergyDlvd")
    net_consumption_actEnergyRcvd = data[1].get("actEnergyRcvd")    
    net_consumption_power = data[1].get("activePower")
    net_consumption_voltage = data[1].get("voltage")
    net_consumption_current = data[1].get("current")
    net_consumption_freq = data[1].get("freq")

    # calculated import export values
    power_consumption = max(0, production_power + net_consumption_power)
    power_export = max(0, production_power - power_consumption)
    power_import = max(0, power_consumption - production_power)

    production_power_dlvd_over_time = 0
    production_power_rcvd_over_time = 0
    net_consumption_power_dlvd_over_time = 0
    net_consumption_power_rcvd_over_time = 0

    # calculate over time powers
    if last_run_data.last_run_time is not None:
        time_diff_seconds = (data_timestamp - last_run_data.last_run_time).total_seconds()
        print(f"Time since last run: {time_diff_seconds} seconds")
        production_power_dlvd_over_time = (production_actEnergyDlvd - last_run_data.last_production_actEnergyDlvd) / (time_diff_seconds / 3600)
        production_power_rcvd_over_time = (production_actEnergyRcvd - last_run_data.last_production_actEnergyRcvd) / (time_diff_seconds / 3600)
        net_consumption_power_dlvd_over_time = (net_consumption_actEnergyDlvd - last_run_data.last_net_consumption_actEnergyDlvd) / (time_diff_seconds / 3600)
        net_consumption_power_rcvd_over_time = (net_consumption_actEnergyRcvd - last_run_data.last_net_consumption_actEnergyRcvd) / (time_diff_seconds / 3600)
 
    # update last run data
    last_run_data.last_production_actEnergyDlvd = production_actEnergyDlvd
    last_run_data.last_production_actEnergyRcvd = production_actEnergyRcvd
    last_run_data.last_net_consumption_actEnergyDlvd = net_consumption_actEnergyDlvd
    last_run_data.last_net_consumption_actEnergyRcvd = net_consumption_actEnergyRcvd
    last_run_data.last_run_time = data_timestamp

    eot = net_consumption_power_rcvd_over_time
    iot = net_consumption_power_dlvd_over_time
    pot = production_power_dlvd_over_time
    cot = (pot - eot) + iot

    if verbose:
        print("*" * 80)
        print(f"Timestamp : {timestamp_str}")

        print(f"Production T      : {production_actEnergyDlvd}\t{production_actEnergyRcvd}")
        print(f"NetConsumption T  : {net_consumption_actEnergyDlvd}\t{net_consumption_actEnergyRcvd}")
        print(f"Production Power Dlvd Over Time : {production_power_dlvd_over_time} W")
        print(f"Production Power Rcvd Over Time : {production_power_rcvd_over_time} W")
        print(f"Net Consumption Power Dlvd Over Time : {net_consumption_power_dlvd_over_time} W")
        print(f"Net Consumption Power Rcvd Over Time : {net_consumption_power_rcvd_over_time} W")

        print("")

        print(f"Production Over Time (POT) : {pot} W")
        print(f"Energy Export Over Time (EOT) : {eot} W")
        print(f"Energy In Over Time (IOT) : {iot} W")
        print(f"Consumption Over Time (COT) : {cot} W")

        print("")

        print(f"Production        : {production_power} W\t{production_voltage} V\t{production_current} A\t{production_freq} Hz")
        print(f"NetConsumption    : {net_consumption_power} W\t{net_consumption_voltage} V\t{net_consumption_current} A\t{net_consumption_freq} Hz")

        print(f"Power Used        : {power_consumption} W")
        print(f"Power Export      : {power_export} W")
        print(f"Power Import      : {power_import} W")


    # build log data
    date_string = data_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    log_data = {
        "event_date": date_string,
        "event_type": "power",
        "event_data": {
            "pp": production_power, 
            "pv": production_voltage,
            "pc": production_current,
            "pf": production_freq,
            "ncp": net_consumption_power,
            "ncv": net_consumption_voltage,
            "ncc": net_consumption_current,
            "ncf": net_consumption_freq,
            "apc": power_consumption,
            "ape": power_export,
            "api": power_import,
            "pot": pot,
            "eot": eot,
            "iot": iot,
            "cot": cot
            }
    }
    log_data_row = [log_data]
    request_data = {"electricity": log_data_row}
    if verbose:
        print(json.dumps(request_data, indent=2))

    telemetry_url = config['telemetry']['collection_url']
    r = requests.post(telemetry_url, json=request_data)
    print(date_string + " - New Data Notification Request : " + r.text)

    return 0


if __name__ == "__main__":

    config = load_config()
    verbose = config['telemetry'].get('verbose', False)
    last_run_data = LastRunData()

    while True:
        main(config, last_run_data, verbose)
        time.sleep(60)

