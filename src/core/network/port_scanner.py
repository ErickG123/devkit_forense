import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Optional, Set

TCP_PROBES: Dict[int, bytes] = {
    80: b"HEAD / HTTP/1.1\r\nHost: target\r\n\r\n",
    21: b"FEAT\r\n",
}

PORT_ALERTS: Dict[int, str] = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 137: "NetBIOS-NS", 139: "NetBIOS", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
    1900: "UPnP", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 8080: "HTTP-Proxy",
}

def _clean_banner(banner_bytes: bytes) -> str:
    try:
        banner_str = banner_bytes.decode(errors='ignore')
        printable_banner = "".join(char for char in banner_str if char.isprintable() or char.isspace())
        return printable_banner.strip()
    except Exception:
        return "Falha ao decodificar banner"

def parse_ports(port_str: str) -> List[int]:
    ports: Set[int] = set()
    try:
        parts = port_str.split(',')
        for part in parts:
            if '-' in part:
                start, end = map(int, part.split('-'))
                ports.update(range(start, end + 1))
            else:
                ports.add(int(part))
    except ValueError:
        raise ValueError("Formato de porta inválido. Use '80', '22,80,443' ou '1-1024'.")

    return sorted(list(ports))

def _scan_tcp(ip: str, port: int, timeout: float) -> Optional[Dict]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((ip, port)) == 0:
                banner = ""
                if port == 443:
                    try:
                        context = ssl.create_default_context()
                        with context.wrap_socket(s, server_hostname=ip) as ss:
                            cert = ss.getpeercert()
                            subject = dict(x[0] for x in cert.get('subject', []))
                            banner = f"SSL Cert for: {subject.get('commonName', 'N/A')}"
                    except Exception:
                        banner = "SSL Handshake Error"
                else:
                    try:
                        if port in TCP_PROBES:
                            s.send(TCP_PROBES[port])
                        raw_banner = s.recv(1024)
                        cleaned_banner = _clean_banner(raw_banner)
                        if port in [80, 8080] and cleaned_banner:
                            banner = cleaned_banner.splitlines()[0]
                        else:
                            banner = cleaned_banner
                    except (socket.timeout, ConnectionResetError):
                        pass

                return {
                    "port": port, "protocol": "TCP", "status": "open",
                    "banner": banner or "sem banner",
                    "service": PORT_ALERTS.get(port, "unknown")
                }
    except (socket.timeout, OSError):
        pass

    return None

def _scan_udp(ip: str, port: int, timeout: float) -> Optional[Dict]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            s.sendto(b"", (ip, port))
            try:
                s.recvfrom(1024)
                return {
                    "port": port, "protocol": "UDP", "status": "open",
                    "banner": "response received",
                    "service": PORT_ALERTS.get(port, "unknown")
                }
            except socket.timeout:
                return {
                    "port": port, "protocol": "UDP", "status": "open|filtered",
                    "banner": "no response",
                    "service": PORT_ALERTS.get(port, "unknown")
                }
    except (OSError, socket.timeout):
        pass

    return None

def scan_host(
    target: str,
    ports: str,
    udp: bool = False,
    workers: int = 100,
    timeout: float = 1.0,
    callback: Optional[Callable] = None
) -> List[Dict]:
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        raise ValueError(f"Hostname '{target}' não pôde ser resolvido.")

    tcp_ports_to_scan = parse_ports(ports)
    udp_ports_to_scan = parse_ports("53,67,68,161,500") if udp else []
    
    total_ports = len(tcp_ports_to_scan) + len(udp_ports_to_scan)
    if total_ports == 0:
        return []

    results: List[Dict] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_scan_tcp, ip, port, timeout) for port in tcp_ports_to_scan]
        futures += [executor.submit(_scan_udp, ip, port, timeout) for port in udp_ports_to_scan]

        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
            
            if callback:
                callback()

    results.sort(key=lambda x: x["port"])

    return results
