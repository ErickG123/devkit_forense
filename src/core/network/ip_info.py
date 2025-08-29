import typer
import ipwhois

def ip_info_lookup(ip):
    try:
        obj = ipwhois.IPWhois(ip)
        res = obj.lookup_rdap()

        return {
            "ip": ip,
            "asn": res.get("asn"),
            "asn_country": res.get("asn_country_code"),
            "network_name": res.get("network", {}).get("name"),
            "org": res.get("network", {}).get("org"),
            "cidr": res.get("network", {}).get("cidr")
        }
    except Exception:
        return {"ip": ip, "error": "Não foi possível obter informações"}

def ip_info_batch(ips):
    results = []

    typer.echo(f"[+] Iniciando IP Info Lookup ({len(ips)} IPs)...")
    with typer.progressbar(ips, label="IP Info") as progress:
        for ip in ips:
            results.append(ip_info_lookup(ip))
            progress.update(1)

    return results
