import socket
import typer
import json
import csv
from pathlib import Path

COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "webmail", "smtp", "imap", "pop", "vpn",
    "portal", "intranet", "extranet", "remote", "login", "sso", "admin",
    "test", "dev", "staging", "qa", "demo", "beta", "preprod",
    "api", "api1", "api2", "graphql",
    "db", "database", "mysql", "postgres", "mongo", "redis", "mssql",
    "files", "ftp", "storage", "cdn", "download", "uploads",
    "secure", "firewall", "monitor", "logs", "siem",
    "ns1", "ns2", "ns3", "dns1", "dns2",
    "cloud", "aws", "azure", "gcp",
    "shop", "store", "payment", "support", "helpdesk", "status"
]

def reverse_dns(ip: str):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)

        return {"ip": ip, "hostname": hostname}
    except socket.herror:
        return {"ip": ip, "hostname": "N/A"}

def dns_lookup(domain: str):
    try:
        host, _, ips = socket.gethostbyname_ex(domain)

        return {"domain": domain, "ips": ips}
    except socket.gaierror:
        return {"domain": domain, "ips": []}

def brute_subdomains(domain: str):
    found = []
    for sub in COMMON_SUBDOMAINS:
        subdomain = f"{sub}.{domain}"
        try:
            host, _, ips = socket.gethostbyname_ex(subdomain)
            found.append({"domain": subdomain, "ips": ips})
        except socket.gaierror:
            continue

    return found

def save_results(results: list, output_dir: str, filename: str = "dns_recon"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    json_file = Path(output_dir) / f"{filename}.json"
    csv_file = Path(output_dir) / f"{filename}.csv"

    with open(json_file, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=4, ensure_ascii=False)

    with open(csv_file, "w", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["domain", "ips", "hostname", "ip"])
        for item in results:
            writer.writerow([
                item.get("domain", ""),
                ", ".join(item.get("ips", [])),
                item.get("hostname", ""),
                item.get("ip", "")
            ])

    return {"json_file": str(json_file), "csv_file": str(csv_file)}

def dns_recon(ips_or_domains: list[str], output_dir: str = None, with_subdomains: bool = False):
    results = []

    typer.echo(f"[+] Iniciando DNS Recon ({len(ips_or_domains)} alvos)...")
    with typer.progressbar(ips_or_domains, label="DNS Recon") as progress:
        for target in progress:
            if target.count(".") == 3 and all(x.isdigit() for x in target.split(".")):
                results.append(reverse_dns(target))
            else:
                result = dns_lookup(target)
                results.append(result)

                if with_subdomains:
                    subs = brute_subdomains(target)
                    results.extend(subs)

    if output_dir:
        files = save_results(results, output_dir)
        typer.echo(f"[+] Resultados salvos em {files['json_file']} e {files['csv_file']}")

    return results
