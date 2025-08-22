import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import csv

COMMON_TCP_PORTS = [21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445,
                    3389, 3306, 8080, 8443, 5900, 135, 995, 993, 1723]

COMMON_UDP_PORTS = [53, 69, 123, 161, 162, 500, 514]

PORT_ALERTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    443: "HTTPS",
    445: "SMB",
    3306: "MySQL",
    3389: "RDP"
}

def scan_tcp(ip, port, results):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex((ip, port)) == 0:
                banner = ""
                try:
                    if port == 80 or port == 443:
                        s.send(b"HEAD / HTTP/1.0\r\n\r\n")
                        banner = s.recv(1024).decode(errors="ignore").strip()
                except:
                    pass
                results.append({
                    "port": port,
                    "protocol": "TCP",
                    "status": "open",
                    "banner": banner if banner else "sem banner",
                    "alert": PORT_ALERTS.get(port)
                })
    except:
        pass

def scan_udp(ip, port, results):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(1)
            s.sendto(b"", (ip, port))
            try:
                data, _ = s.recvfrom(1024)
                banner = data.decode(errors="ignore").strip()
            except:
                banner = "sem resposta"
            results.append({
                "port": port,
                "protocol": "UDP",
                "status": "open|filtered",
                "banner": banner,
                "alert": PORT_ALERTS.get(port)
            })
    except:
        pass

def scan_host(ip, tcp_ports=None, udp_ports=None):
    tcp_ports = tcp_ports or COMMON_TCP_PORTS
    udp_ports = udp_ports or COMMON_UDP_PORTS
    results = []

    with ThreadPoolExecutor(max_workers=100) as executor:
        for port in tcp_ports:
            executor.submit(scan_tcp, ip, port, results)
        for port in udp_ports:
            executor.submit(scan_udp, ip, port, results)
    
    return results

def save_results(results, ip):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"scan_{ip}_{timestamp}.json"
    csv_file = f"scan_{ip}_{timestamp}.csv"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["port", "protocol", "status", "banner", "alert"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"✅ Resultados salvos em JSON: {json_file} e CSV: {csv_file}")

if __name__ == "__main__":
    ip = input("Digite o IP do host a escanear: ")
    print(f"\n[+] Escaneando {ip}...")
    host_results = scan_host(ip)
    
    for r in host_results:
        alert_msg = f" | ALERT: {r['alert']}" if r['alert'] else ""
        print(f"Porta {r['port']} ({r['protocol']}) aberta | {r['banner'][:60]}{alert_msg}")

    save_results(host_results, ip)
