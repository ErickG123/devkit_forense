import os
import json
import csv
from datetime import datetime
import threading
import typer

from core.network.ping_sweep import ping_sweep
from core.network.arp_scan import arp_scan
from core.network.port_scanner import scan_host
from core.network.utils import get_mac, get_vendor, get_hostname
from core.network.fingerprinting import detect_os
from core.network.traceroute import traceroute_host
from core.network.snmp_scan import snmp_scan
from core.network.dns_recon import dns_recon
from core.network.smb_scan import smb_scan
from core.network.ip_info import ip_info_lookup

lock = threading.Lock()

def build_network_map(network):
    hosts = ping_sweep(network)
    if not hosts:
        hosts = arp_scan(network)

    results = []

    typer.echo(f"[+] Iniciando varredura da rede ({len(hosts)} hosts)...")

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

            hops = traceroute_host(host)

            snmp_info = snmp_scan(host)

            dns_info = dns_recon([host])

            smb_info = smb_scan([host])

            ip_info = ip_info_lookup(host)

            host_data = {
                "host": host,
                "hostname": hostname,
                "mac": mac,
                "vendor": vendor,
                "open_ports": open_ports,
                "os_info": os_info,
                "traceroute": hops,
                "snmp": snmp_info,
                "dns": dns_info[0] if dns_info else {},
                "smb": smb_info[0] if smb_info else {},
                "ip_info": ip_info
            }

            with lock:
                results.append(host_data)

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
        fieldnames = ["host", "hostname", "mac", "vendor", "os_type", "host_type",
                      "open_ports_count", "traceroute_hops", "snmp_sys_name", "dns_hostname",
                      "smb_shares_count", "vulnerabilities_count", "asn", "network_name"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            writer.writerow({
                "host": row["host"],
                "hostname": row["hostname"],
                "mac": row["mac"],
                "vendor": row["vendor"],
                "os_type": row["os_info"].get("os"),
                "host_type": row["os_info"].get("host_type"),
                "open_ports_count": len(row["open_ports"]),
                "traceroute_hops": len(row["traceroute"]),
                "snmp_sys_name": row["snmp"].get("sys_name"),
                "dns_hostname": row["dns"].get("hostname"),
                "smb_shares_count": len(row["smb"].get("shares", [])),
                "asn": row["ip_info"].get("asn"),
                "network_name": row["ip_info"].get("network_name"),
            })

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
