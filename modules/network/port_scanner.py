import socket
import json
import csv
import argparse
import platform
import subprocess
from datetime import datetime
from tqdm import tqdm

def is_host_up(host):
    """Verifica se o host está ativo usando ping"""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        subprocess.check_output(["ping", param, "1", host], stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def detect_banner(sock, host, port):
    """Tenta identificar o banner de um serviço"""
    try:
        sock.settimeout(2)
        if port == 80:
            sock.send(b"HEAD / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
        banner = sock.recv(1024)
        return banner.decode(errors='ignore').strip()
    except:
        return "N/A"

def scan_port(host, port):
    """Escaneia uma única porta"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                banner = detect_banner(sock, host, port)
                return {"port": port, "status": "open", "banner": banner}
    except:
        pass
    return None

def save_results(results, filename, format="json"):
    """Salva os resultados em JSON ou CSV"""
    if format == "json":
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
    elif format == "csv":
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["host", "port", "banner"])
            writer.writeheader()
            for item in results:
                writer.writerow(item)

def main():
    parser = argparse.ArgumentParser(description="Scanner de portas e detecção de banners")
    parser.add_argument("host", help="Endereço IP ou hostname do alvo")
    parser.add_argument("--intenso", action="store_true", help="Escanear da porta 1 até 1024")
    parser.add_argument("--todas", action="store_true", help="Escanear todas as 65535 portas")
    parser.add_argument("--saida", help="Salvar resultado em arquivo (JSON ou CSV)")
    parser.add_argument("--formato", choices=["json", "csv"], default="json", help="Formato de saída")
    args = parser.parse_args()

    host = args.host
    print(f"\n[+] Iniciando varredura em {host} - {datetime.now().strftime('%H:%M:%S')}")
    
    if not is_host_up(host):
        print(f"[-] Host {host} inativo ou inacessível.\n")
        return

    if args.todas:
        portas = range(1, 65536)
    elif args.intenso:
        portas = range(1, 1025)
    else:
        portas = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389]

    resultados = []

    for porta in tqdm(portas, desc="Escaneando"):
        resultado = scan_port(host, porta)
        if resultado:
            resultado["host"] = host
            resultados.append(resultado)
            print(f"[+] Porta {porta} aberta | Banner: {resultado['banner'][:60]}")

    if args.saida:
        save_results(resultados, args.saida, args.formato)
        print(f"\n[✔] Resultados salvos em: {args.saida}")

    print("\n[✓] Varredura finalizada.")

if __name__ == "__main__":
    main()
