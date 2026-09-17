"""
Módulo de Fingerprinting de Rede (v2 Híbrido).

Utiliza o Go Core para varredura de portas TCP Connect em alta velocidade e executa
banner grabbing / heurística de SO apenas nos serviços ativos identificados.
"""

from __future__ import annotations

import platform
import re
import socket
import subprocess
from typing import Any

SERVER_TYPE_MAP = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "Web HTTP",
    110: "POP3",
    135: "RPC / Endpoint Mapper",
    139: "NetBIOS / SMB",
    143: "IMAP",
    443: "Web HTTPS",
    445: "Microsoft SMB",
    3306: "MySQL Database",
    3389: "Microsoft RDP",
    5432: "PostgreSQL Database",
    5900: "VNC Remote Desktop",
    8080: "HTTP Proxy / Alternate",
}

VERSION_ALERTS = {
    "vsftpd 2.3.4": "Backdoor histórico conhecido (CVE-2011-2523)",
    "openssh 5.3": "Versão obsoleta de OpenSSH sem suporte a algoritmos modernos",
    "samba 3.0": "Versão desatualizada de Samba vulnerável a RCE",
    "apache 2.2": "Servidor Apache legado em fim de vida",
}


def grab_banner(ip: str, port: int, timeout: float = 1.0) -> str:
    """Tenta obter o banner do serviço conectando apenas na porta aberta."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, port))

            # Probes direcionados para protocolos comuns
            if port in (80, 8080):
                s.sendall(b"HEAD / HTTP/1.0\r\nHost: " + ip.encode() + b"\r\n\r\n")
            elif port == 21:
                pass  # FTP envia banner inicial automático
            elif port == 22:
                pass  # SSH envia identificação de versão inicial
            elif port == 25:
                pass  # SMTP envia banner 220

            data = s.recv(1024)
            if data:
                text = data.decode("utf-8", errors="ignore").strip()
                # Pega a primeira linha relevante do banner
                first_line = text.splitlines()[0] if text.splitlines() else text
                return first_line[:120]
    except Exception:
        pass
    return ""


def detect_os_by_ttl(ip: str) -> str:
    """Estima a família do SO inspecionando o TTL retornado pelo ping ICMP do sistema operacional."""
    try:
        ping_cmd = (
            ["ping", "-n", "1", "-w", "1000", ip]
            if platform.system() == "Windows"
            else ["ping", "-c", "1", "-W", "1", ip]
        )
        proc = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=2.0)
        output = proc.stdout.lower()

        for line in output.splitlines():
            if "ttl=" in line:
                part = line.split("ttl=")[1].split()[0]
                ttl = int(re.sub(r"[^\d]", "", part))
                if ttl <= 64:
                    return "Linux / Unix (TTL <= 64)"
                elif ttl <= 128:
                    return "Windows (TTL <= 128)"
                elif ttl <= 255:
                    return "Cisco / Roteador / Solaris (TTL <= 255)"
    except Exception:
        pass
    return "Desconhecido / ICMP Bloqueado"


def analyze_fingerprint(ip: str, open_ports: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Consolida as portas abertas fornecidas pelo motor Go, analisa banners
    e infere o perfil do host alvo.
    """
    os_estimate = detect_os_by_ttl(ip)
    services: list[str] = []
    alerts: list[str] = []
    enriched_ports: list[dict[str, Any]] = []

    for item in open_ports:
        port = int(item.get("port", 0))
        banner = item.get("banner", "")

        # Se o banner não veio do Go, tenta grab direcionado
        if not banner:
            banner = grab_banner(ip, port)

        service_name = SERVER_TYPE_MAP.get(port, f"Porta {port}/TCP")
        services.append(service_name)

        banner_lower = banner.lower()
        if any(w in banner_lower for w in ("microsoft", "windows", "iis", "msrpc")):
            os_estimate = "Microsoft Windows Server/Desktop"
        elif any(w in banner_lower for w in ("ubuntu", "debian", "centos", "red hat", "linux", "unix")):
            os_estimate = "Linux / Unix Server"

        # Verificação de alertas conhecidos
        for sig, alert_msg in VERSION_ALERTS.items():
            if sig in banner_lower:
                alerts.append(f"{service_name}: {alert_msg}")

        enriched_ports.append({
            "port": port,
            "service": service_name,
            "banner": banner or "-",
            "latency_ms": item.get("latency_ms", 0),
        })

    # Classificação de host
    port_numbers = [p["port"] for p in enriched_ports]
    server_ports = {21, 22, 25, 53, 80, 443, 445, 3306, 5432}
    host_type = "Servidor / Infraestrutura" if set(port_numbers) & server_ports else "Desktop / Endpoint"

    return {
        "ip": ip,
        "os": os_estimate,
        "host_type": host_type,
        "total_open": len(enriched_ports),
        "ports": enriched_ports,
        "services": services,
        "alerts": alerts,
    }
