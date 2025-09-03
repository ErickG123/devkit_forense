import typer
import ipaddress
from scapy.all import ARP, Ether, srp, sr1, IP, ICMP

def is_valid_ip(addr: str) -> bool:
    try:
        ipaddress.ip_address(addr)
        return True
    except ValueError:
        return False

def arp_scan(network_ips):
    active_hosts = []

    ips = [ip for ip in network_ips if is_valid_ip(ip)]

    typer.echo(f"[+] Iniciando ARP scan ({len(ips)} IPs)...")

    with typer.progressbar(ips, label="ARP Scan") as progress:
        for ip in ips:
            try:
                pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
                ans, _ = srp(pkt, timeout=1, verbose=0)
                if ans:
                    active_hosts.append(ip)

            except Exception:
                try:
                    pkt = IP(dst=ip) / ICMP()
                    resp = sr1(pkt, timeout=1, verbose=0)
                    if resp:
                        active_hosts.append(ip)
                except Exception:
                    pass

            progress.update(1)

    return active_hosts
