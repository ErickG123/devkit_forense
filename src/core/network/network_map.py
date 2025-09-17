import os
import json
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import typer

from .ping_sweep import ping_sweep
from .arp_scan import arp_scan
from .port_scanner import scan_host
from .utils import get_mac, get_vendor, get_hostname
from .fingerprinting import detect_os
from .traceroute import traceroute_host
from .snmp_scan import snmp_scan
from .dns_recon import dns_recon
from .smb_scan import smb_scan
from .ip_info import ip_info_lookup

def _process_host(host: str, ports_to_scan: str) -> dict:
    open_ports = scan_host(host, ports=ports_to_scan)

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

    return {
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

def build_network_map(network: str, ports: str, workers: int = 50):
    hosts = ping_sweep(network)
    if not hosts:
        typer.echo("[+] Ping sweep não encontrou hosts, tentando ARP scan...")
        hosts = arp_scan(network)

    if not hosts:
        typer.echo("[!] Nenhum host ativo encontrado na rede especificada.")
        return []

    results = []
    typer.echo(f"[+] {len(hosts)} host(s) ativo(s) encontrado(s). Iniciando análise detalhada...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_host = {executor.submit(_process_host, host, ports): host for host in hosts}

        with typer.progressbar(as_completed(future_to_host), length=len(hosts), label="Mapeando Rede") as progress:
            for future in progress:
                try:
                    host_data = future.result()
                    results.append(host_data)
                except Exception as exc:
                    host = future_to_host[future]
                    typer.echo(f"\n[!] Erro ao processar o host {host}: {exc}")
    
    return results

def save_network_map(results: list, output_dir: str, prefix="network_map"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file = os.path.join(output_dir, f"{prefix}_{timestamp}.json")
    csv_file = os.path.join(output_dir, f"{prefix}_{timestamp}.csv")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    flat_results = []
    for row in results:
        flat_row = {
            "host": row.get("host"),
            "hostname": row.get("hostname"),
            "mac": row.get("mac"),
            "vendor": row.get("vendor"),
            "os_type": row.get("os_info", {}).get("os"),
            "host_type": row.get("os_info", {}).get("host_type"),
            "open_ports_count": len(row.get("open_ports", [])),
            "traceroute_hops": len(row.get("traceroute", [])),
            "snmp_sys_name": row.get("snmp", {}).get("sys_name"),
            "dns_hostname": row.get("dns", {}).get("hostname"),
            "smb_shares_count": len(row.get("smb", {}).get("shares", [])),
            "asn": row.get("ip_info", {}).get("asn"),
            "network_name": row.get("ip_info", {}).get("network_name"),
        }
        flat_results.append(flat_row)
        
    if not flat_results:
        return json_file, None

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = flat_results[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_results)

    return json_file, csv_file

def run(network: str, ports: str, output_dir: str, prefix="network_map"):
    results = build_network_map(network, ports)
    
    if results:
        json_file, csv_file = save_network_map(results, output_dir, prefix)
        return {"results": results, "json_file": json_file, "csv_file": csv_file}
    else:
        return {}
