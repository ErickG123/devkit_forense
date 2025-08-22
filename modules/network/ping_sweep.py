from scapy.all import ARP, Ether, srp, conf
import socket
from utils import get_mac, get_vendor, get_hostname
import json
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

COMMON_TCP = [21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445,
              3389, 3306, 8080, 8443, 5900, 135, 995, 993, 1723]

COMMON_UDP = [53, 67, 68, 69, 123, 161, 162, 500, 514, 520]

CRITICAL_PORTS = {
    21: "FTP (Possível vulnerável)",
    22: "SSH (Verificar força/brute-force)",
    23: "Telnet (Vulnerável)",
    139: "SMB (Vulnerável, Windows antigo)",
    445: "SMB (Vulnerável, Windows antigo)",
    3306: "MySQL exposto",
    3389: "RDP exposto"
}

def scan_tcp_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, port))
        banner = ""
        if result == 0:
            try:
                sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                banner = sock.recv(1024).decode(errors="ignore").strip()
            except:
                pass
            alert = CRITICAL_PORTS.get(port, "")
            return {"port": port, "protocol": "TCP", "banner": banner if banner else "sem banner", "alert": alert}
    except:
        pass
    finally:
        sock.close()
    return None

def scan_udp_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        sock.sendto(b"", (ip, port))
        try:
            data, _ = sock.recvfrom(1024)
            banner = data.decode(errors="ignore")
        except socket.timeout:
            banner = "sem resposta (UDP)"
        alert = CRITICAL_PORTS.get(port, "")
        return {"port": port, "protocol": "UDP", "banner": banner, "alert": alert}
    except:
        pass
    finally:
        sock.close()
    return None

def scan_ports(ip, tcp_ports=COMMON_TCP, udp_ports=COMMON_UDP):
    open_ports = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        tcp_futures = [executor.submit(scan_tcp_port, ip, p) for p in tcp_ports]

        udp_futures = [executor.submit(scan_udp_port, ip, p) for p in udp_ports]

        for f in tcp_futures + udp_futures:
            res = f.result()
            if res:
                open_ports.append(res)

    return open_ports

def ping_sweep(network):
    conf.verb = 0
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=network)
    ans, _ = srp(pkt, timeout=2)
    ativos = []
    for _, rcv in ans:
        ativos.append(rcv[ARP].psrc)
    return ativos

if __name__ == "__main__":
    rede = input("Digite a rede (ex: 192.168.0.0/24): ")

    hosts = ping_sweep(rede)
    resultados = []

    print("\n🔍 Hosts ativos encontrados:")
    for ip in hosts:
        mac = get_mac(ip)
        vendor = get_vendor(mac)
        hostname = get_hostname(ip)
        ports = scan_ports(ip)

        host_info = {
            "ip": ip,
            "mac": mac,
            "vendor": vendor,
            "hostname": hostname,
            "ports": ports
        }
        resultados.append(host_info)

        print(f"\nIP: {ip}")
        print(f"  MAC: {mac} ({vendor})")
        print(f"  Hostname: {hostname}")
        if ports:
            print("  Portas abertas:")
            for p in ports:
                alert_str = f"⚠️ {p['alert']}" if p['alert'] else ""
                print(f"    - {p['protocol']} {p['port']} | {p['banner']} {alert_str}")
        else:
            print("  Nenhuma porta aberta encontrada.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"network_scan_{timestamp}.json"
    csv_file = f"network_scan_{timestamp}.csv"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Resultados salvos em JSON: {json_file}")

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["IP", "MAC", "Vendor", "Hostname", "Protocolo", "Porta", "Banner", "Alerta"])
        for r in resultados:
            for p in r["ports"]:
                writer.writerow([r["ip"], r["mac"], r["vendor"], r["hostname"], p["protocol"], p["port"], p["banner"], p["alert"]])
    print(f"✅ Resultados salvos em CSV: {csv_file}")
