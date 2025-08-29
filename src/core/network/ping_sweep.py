import platform
import subprocess

from scapy.all import conf

conf.verb = 0

def ping_sweep(network):
    hosts = []
    
    if "-" in network:
        base_ip = network.rsplit(".", 1)[0]
        start, end = network.rsplit(".", 1)[1].split("-")
        ip_range = [f"{base_ip}.{i}" for i in range(int(start), int(end)+1)]
    else:
        ip_range = [network]

    for ip in ip_range:
        if platform.system() == "Windows":
            try:
                output = subprocess.run(
                    ["ping", "-n", "1", "-w", "500", ip],
                    capture_output=True,
                    text=True
                )
                if "TTL=" in output.stdout.upper():
                    hosts.append(ip)
            except:
                continue
        else:
            from scapy.all import ARP, Ether, srp
            pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
            ans, _ = srp(pkt, timeout=1, verbose=0)
            if ans:
                hosts.append(ip)

    return hosts
