import platform
import subprocess
from scapy.all import conf, ARP, Ether, srp
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import typer

conf.verb = 0
lock = threading.Lock()

def parse_network(network: str):
    if "-" in network:
        base_ip = network.rsplit(".", 1)[0]
        start, end = network.rsplit(".", 1)[1].split("-")
        return [f"{base_ip}.{i}" for i in range(int(start), int(end)+1)]
    else:
        return [network]

def ping_host(ip: str) -> bool:
    try:
        if platform.system() == "Windows":
            output = subprocess.run(
                ["ping", "-n", "1", "-w", "500", ip],
                capture_output=True,
                text=True
            )
            return "TTL=" in output.stdout.upper()
        else:
            pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
            ans, _ = srp(pkt, timeout=1, verbose=0)
            return bool(ans)
    except Exception:
        return False

def ping_sweep(network: str):
    ips = parse_network(network)
    hosts = []

    with typer.progressbar(ips, label="Ping Sweep") as progress:
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(ping_host, ip): ip for ip in ips}

            for future in as_completed(futures):
                ip = futures[future]
                try:
                    if future.result():
                        with lock:
                            hosts.append(ip)
                except Exception:
                    pass
                progress.update(1)

    return hosts
