import subprocess
import platform
import re

SERVER_PORTS = [21, 22, 23, 25, 53, 80, 443, 139, 445, 3306, 3389]
SERVER_TYPE_MAP = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "Web HTTP",
    443: "Web HTTPS",
    139: "SMB",
    445: "SMB",
    3306: "MySQL",
    3389: "RDP"
}

VERSION_ALERTS = {
    "ftp": ["vsftpd 2.3.4"],
    "ssh": ["OpenSSH 5.3"],
    "smb": ["Samba 3.0"],
    "mysql": ["MySQL 5.5"]
}

def extract_service_version(banner):
    if not banner:
        return None
    match = re.search(r"([a-zA-Z]+)[ /]?([0-9]+\.[0-9]+(?:\.[0-9]+)?)", banner)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return banner.strip() if banner else None

def detect_os(ip, ports=None, mac_vendor=None):
    os_estimate = "Desconhecido"
    host_type = "Desconhecido"
    services = []
    alerts = []

    try:
        ping_cmd = ["ping", "-c", "1", "-W", "1", ip] if platform.system() != "Windows" else ["ping", "-n", "1", "-w", "1000", ip]
        ping_proc = subprocess.run(ping_cmd, capture_output=True, text=True)
        output = ping_proc.stdout
        ttl_line = next((line for line in output.splitlines() if "ttl=" in line.lower()), None)
        if ttl_line:
            ttl = int(ttl_line.lower().split("ttl=")[1].split()[0])
            if ttl <= 64:
                os_estimate = "Linux/Unix"
            elif ttl <= 128:
                os_estimate = "Windows"
    except:
        os_estimate = "Host inatingível"

    if ports:
        for p in ports:
            banner = p.get("banner", "").lower()
            service_name = SERVER_TYPE_MAP.get(p["port"], f"Port {p['port']}")
            services.append(service_name)

            if any(x in banner for x in ["microsoft", "windows"]):
                os_estimate = "Windows"
            elif any(x in banner for x in ["linux", "ubuntu", "debian", "centos", "red hat"]):
                os_estimate = "Linux/Unix"

            for key, vulnerable_versions in VERSION_ALERTS.items():
                if key in banner:
                    for v in vulnerable_versions:
                        if v.lower() in banner:
                            alerts.append(f"{service_name} vulnerável ({v})")

            version = extract_service_version(p.get("banner"))
            if version:
                p["version"] = version

    if mac_vendor:
        vendor = mac_vendor.lower()
        if any(x in vendor for x in ["cisco", "huawei", "juniper", "mikrotik"]):
            os_estimate = "Dispositivo de rede"
            host_type = "Roteador/Switch"

    if ports and host_type == "Desconhecido":
        port_numbers = [p["port"] for p in ports]
        server_ports = [p for p in SERVER_PORTS if p in port_numbers]
        if server_ports:
            host_type = "Servidor"
        else:
            host_type = "Desktop"

    return {
        "os": os_estimate,
        "host_type": host_type,
        "services": services,
        "alerts": alerts
    }
