import socket
import typer

def reverse_dns(ip):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)

        return {"ip": ip, "hostname": hostname}
    except socket.herror:
        return {"ip": ip, "hostname": "N/A"}

def dns_lookup(domain):
    try:
        ip = socket.gethostbyname(domain)
        return {"domain": domain, "ip": ip}
    except socket.gaierror:
        return {"domain": domain, "ip": None}

def dns_recon(ips_or_domains):
    results = []

    typer.echo(f"[+] Iniciando DNS Recon ({len(ips_or_domains)} alvos)...")
    with typer.progressbar(ips_or_domains, label="DNS Recon") as progress:
        for target in ips_or_domains:
            if target.count(".") == 3 and all(x.isdigit() for x in target.split(".")):
                results.append(reverse_dns(target))
            else:
                results.append(dns_lookup(target))
            progress.update(1)

    return results
