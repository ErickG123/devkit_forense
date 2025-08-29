import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import typer

COMMON_TCP_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445,
    3389, 3306, 8080, 8443, 5900, 135, 995, 993, 1723
]
COMMON_UDP_PORTS = [53, 67, 68, 69, 123, 161, 162, 500, 514]

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

lock = threading.Lock()

def scan_tcp(ip, port):
    result = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex((ip, port)) == 0:
                banner = ""
                try:
                    if port in [21, 22, 25, 80, 443, 3306]:
                        s.send(b"HEAD / HTTP/1.0\r\n\r\n")
                        banner = s.recv(1024).decode(errors="ignore").strip()
                except (socket.timeout, ConnectionResetError):
                    pass

                result = {
                    "port": port,
                    "protocol": "TCP",
                    "status": "open",
                    "banner": banner if banner else "sem banner",
                    "alert": PORT_ALERTS.get(port)
                }
    except (socket.timeout, OSError):
        pass
    return result

def scan_udp(ip, port):
    result = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(1)
            s.sendto(b"", (ip, port))
            try:
                data, _ = s.recvfrom(1024)
                banner = data.decode(errors="ignore").strip()
                status = "open"
            except socket.timeout:
                banner = "sem resposta"
                status = "open|filtered"
            result = {
                "port": port,
                "protocol": "UDP",
                "status": status,
                "banner": banner,
                "alert": PORT_ALERTS.get(port)
            }
    except (OSError, socket.timeout):
        pass
    return result

def scan_host(ip, tcp_ports=None, udp_ports=None):
    tcp_ports = tcp_ports or COMMON_TCP_PORTS
    udp_ports = udp_ports or COMMON_UDP_PORTS
    all_ports = tcp_ports + udp_ports
    results = []

    with typer.progressbar(all_ports, label=f"Scanning {ip}") as progress:
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(scan_tcp if port in tcp_ports else scan_udp, ip, port): port for port in all_ports}

            for future in as_completed(futures):
                res = future.result()
                if res:
                    with lock:
                        results.append(res)
                progress.update(1)

    return results
