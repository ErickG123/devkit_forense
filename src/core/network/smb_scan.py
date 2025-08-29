from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
import typer

def smb_scan_host(ip, username="", password=""):
    try:
        conn = Connection(guid=None, server_name=ip, port=445, require_signing=True)
        conn.connect()
        session = Session(conn, username=username, password=password)
        session.connect()

        tree = TreeConnect(session, fr"\\{ip}\IPC$")
        tree.connect()

        shares = ["IPC$"]
        return {"ip": ip, "shares": shares}

    except Exception as e:
        return {"ip": ip, "shares": [], "error": str(e)}


def smb_scan(hosts, username="", password=""):
    results = []

    typer.echo(f"[+] Iniciando SMB Scan ({len(hosts)} hosts)...")
    with typer.progressbar(hosts, label="SMB Scan") as progress:
        for ip in hosts:
            results.append(smb_scan_host(ip, username, password))
            progress.update(1)

    return results
