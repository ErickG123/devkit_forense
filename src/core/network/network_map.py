from core.network.ping_sweep import ping_sweep
from core.network.port_scanner import scan_host
from core.network.utils import get_mac, get_vendor, get_hostname
from core.network.fingerprinting import detect_os

import json
import csv
import os
from datetime import datetime

try:
    from scapy.all import conf
    conf.L2socket
except Exception:
    from scapy.all import conf, L3RawSocket
    conf.L2socket = L3RawSocket

def build_network_map(network: str):
    hosts = ping_sweep(network)
    results = []
    for host in hosts:
        open_ports = scan_host(host)
        
        try:
            mac = get_mac(host)
            vendor = get_vendor(mac) if mac else None
        except Exception:
            mac = None
            vendor = None

        hostname = get_hostname(host)
        os_info = detect_os(host, ports=open_ports, mac_vendor=vendor)

        results.append({
            "host": host,
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor,
            "open_ports": open_ports,
            "os_info": os_info,
        })

    return results

def save_network_map(results, output_dir: str, prefix="network_map"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file = os.path.join(output_dir, f"{prefix}_{timestamp}.json")
    csv_file = os.path.join(output_dir, f"{prefix}_{timestamp}.csv")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["host", "hostname", "mac", "vendor", "open_ports", "os_info"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    return json_file, csv_file

def run(network: str, output_dir: str, prefix="network_map"):
    results = build_network_map(network)
    json_file, csv_file = save_network_map(results, output_dir, prefix)

    return {
        "results": results,
        "json_file": json_file,
        "csv_file": csv_file,
    }
