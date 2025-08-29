from scapy.all import ARP, Ether, srp
import typer

def arp_scan(network_ips):
    active_hosts = []

    typer.echo(f"[+] Iniciando ARP scan ({len(network_ips)} IPs)...")
    with typer.progressbar(network_ips, label="ARP Scan") as progress:
        for ip in network_ips:
            pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
            ans, _ = srp(pkt, timeout=1, verbose=0)
            if ans:
                active_hosts.append(ip)
            progress.update(1)

    return active_hosts
