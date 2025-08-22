from core.network.ping_sweep import ping_sweep
from core.network.port_scanner import scan_host
from core.network.utils import get_mac, get_vendor, get_hostname
from core.network.fingerprinting import detect_os
import json
import csv
from datetime import datetime
import os

def build_network_map(network):
    hosts = ping_sweep(network)
    network_results = []

    print(f"\n🔍 Hosts ativos encontrados: {len(hosts)}")
    for ip in hosts:
        print(f"\n[+] Escaneando host {ip}...")

        mac = get_mac(ip)
        vendor = get_vendor(mac)
        hostname = get_hostname(ip)
        ports = scan_host(ip)
        os_info = detect_os(ip, ports=ports, mac_vendor=vendor)

        host_info = {
            "ip": ip,
            "mac": mac,
            "vendor": vendor,
            "hostname": hostname,
            "os": os_info,
            "ports": ports
        }

        network_results.append(host_info)

        os_str = f"{os_info['os']} ({os_info['host_type']})"
        print(f"IP: {ip} | MAC: {mac} ({vendor}) | Hostname: {hostname} | OS: {os_str}")
        if os_info['services']:
            print(f"  Serviços detectados: {', '.join(os_info['services'])}")
        if os_info['alerts']:
            print(f"  ⚠️ Alertas: {', '.join(os_info['alerts'])}")

        if ports:
            for p in ports:
                alert_msg = f" | ALERT: {p.get('alert')}" if p.get("alert") else ""
                version_msg = f" | Version: {p.get('version')}" if p.get("version") else ""
                print(f"  - {p['port']} ({p['protocol']}) aberta | {p['banner'][:60]}{version_msg}{alert_msg}")
        else:
            print("  Nenhuma porta aberta encontrada.")

    return network_results

def save_network_map(results, output_dir, prefix="network_map"):
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = os.path.join(output_dir, f"{prefix}_{timestamp}.json")
    csv_file = os.path.join(output_dir, f"{prefix}_{timestamp}_advanced.csv")

    service_columns = ["HTTP", "HTTPS", "FTP", "SSH", "SMB", "MySQL", "RDP", "DNS", "Telnet"]
    port_service_map = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        53: "DNS",
        80: "HTTP",
        443: "HTTPS",
        139: "SMB",
        445: "SMB",
        3306: "MySQL",
        3389: "RDP"
    }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        headers = ["IP", "MAC", "Vendor", "Hostname", "OS", "Host_Type", "Alertas"] + service_columns + ["Portas"]
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for host in results:
            service_data = {svc: "" for svc in service_columns}
            for p in host["ports"]:
                svc = port_service_map.get(p["port"])
                if svc:
                    service_data[svc] = "Sim"
            portas_str = ", ".join([f"{p['port']}({p['protocol']}): {p['banner']}{' | Version: '+p['version'] if p.get('version') else ''}" for p in host["ports"]])
            row = {
                "IP": host["ip"],
                "MAC": host["mac"],
                "Vendor": host["vendor"],
                "Hostname": host["hostname"],
                "OS": host["os"]["os"],
                "Host_Type": host["os"]["host_type"],
                "Alertas": ", ".join(host["os"]["alerts"]) if host["os"]["alerts"] else "",
                **service_data,
                "Portas": portas_str
            }
            writer.writerow(row)

    print(f"\n✅ Resultados salvos em JSON: {json_file} e CSV avançado: {csv_file}")

if __name__ == "__main__":
    rede = input("Digite a rede (ex: 192.168.0.0/24): ")
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    OUTPUT_DIR = os.path.join(BASE_DIR, "cli_output")
    network_results = build_network_map(rede)
    save_network_map(network_results, output_dir=OUTPUT_DIR)
