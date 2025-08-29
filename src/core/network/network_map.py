from core.network.ping_sweep import ping_sweep
from core.network.port_scanner import scan_host
from core.network.utils import get_mac, get_vendor, get_hostname
from core.network.fingerprinting import detect_os
from core.network.traceroute import traceroute_host

import json
import csv
import os
from datetime import datetime
import typer
import threading

try:
    from scapy.all import conf
    conf.L2socket
except Exception:
    from scapy.all import conf, L3RawSocket
    conf.L2socket = L3RawSocket

lock = threading.Lock()

def build_network_map(network: str):
    hosts = ping_sweep(network)
    results = []

    typer.echo(f"[+] Iniciando varredura da rede ({len(hosts)} hosts ativos)...")
    with typer.progressbar(hosts, label="Network Map") as progress:
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

            traceroute_result = traceroute_host(host)

            with lock:
                results.append({
                    "host": host,
                    "hostname": hostname,
                    "mac": mac,
                    "vendor": vendor,
                    "open_ports": open_ports,
                    "os_info": os_info,
                    "traceroute": traceroute_result
                })
            progress.update(1)

    return results

def save_network_map(results, output_dir: str, prefix="network_map"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file = os.path.join(output_dir, f"{prefix}_{timestamp}.json")
    csv_file = os.path.join(output_dir, f"{prefix}_{timestamp}.csv")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["host", "hostname", "mac", "vendor", "open_ports", "os_info", "traceroute"])
        writer.writeheader()
        for row in results:
            row_copy = row.copy()
            row_copy["traceroute"] = json.dumps(row_copy["traceroute"], ensure_ascii=False)
            writer.writerow(row_copy)

    return json_file, csv_file

def run(network: str, output_dir: str, prefix="network_map"):
    results = build_network_map(network)
    json_file, csv_file = save_network_map(results, output_dir, prefix)

    typer.echo(f"[+] Network map salvo em: {json_file} e {csv_file}")
    return {
        "results": results,
        "json_file": json_file,
        "csv_file": csv_file,
    }
