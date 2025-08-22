from ping_sweep import ping_sweep
from port_scanner import scan_host
from utils import get_mac, get_vendor, get_hostname
from fingerprinting import detect_os
import json
import csv
from datetime import datetime

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

        print(f"IP: {ip} | MAC: {mac} ({vendor}) | Hostname: {hostname} | OS: {os_info}")
        if ports:
            for p in ports:
                alert_msg = f" | ALERT: {p.get('alert')}" if p.get("alert") else ""
                print(f"  - {p['port']} ({p['protocol']}) aberta | {p['banner'][:60]}{alert_msg}")
        else:
            print("  Nenhuma porta aberta encontrada.")

    return network_results

def save_network_map(results, prefix="network_map"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"{prefix}_{timestamp}.json"
    csv_file = f"{prefix}_{timestamp}_advanced.csv"

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
        headers = ["IP", "MAC", "Vendor", "Hostname", "OS"] + service_columns + ["Portas"]
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for host in results:
            service_data = {svc: "" for svc in service_columns}
            for p in host["ports"]:
                svc = port_service_map.get(p["port"])
                if svc:
                    service_data[svc] = "Sim"
            portas_str = ", ".join([f"{p['port']}({p['protocol']}): {p['banner']}" for p in host["ports"]])
            row = {
                "IP": host["ip"],
                "MAC": host["mac"],
                "Vendor": host["vendor"],
                "Hostname": host["hostname"],
                "OS": host["os"],
                **service_data,
                "Portas": portas_str
            }
            writer.writerow(row)

    print(f"\n✅ Resultados salvos em JSON: {json_file} e CSV avançado: {csv_file}")

if __name__ == "__main__":
    rede = input("Digite a rede (ex: 192.168.0.0/24): ")
    network_results = build_network_map(rede)
    save_network_map(network_results)
