import subprocess
import platform

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

def detect_os(ip, ports=None, mac_vendor=None):
    os_estimate = "Desconhecido"
    host_type = "Desconhecido"
    server_types = []

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
            if any(x in banner for x in ["microsoft", "windows"]):
                os_estimate = "Windows"
            elif any(x in banner for x in ["linux", "ubuntu", "debian", "centos", "red hat"]):
                os_estimate = "Linux/Unix"

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
            for port in server_ports:
                server_types.append(SERVER_TYPE_MAP.get(port))
        else:
            host_type = "Desktop"

    if server_types:
        server_info = ", ".join(server_types)
        return f"{os_estimate} ({host_type}: {server_info})"
    else:
        return f"{os_estimate} ({host_type})"
