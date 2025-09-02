import os
import sqlite3
import time
import json
import shutil
from pathlib import Path

def timestamp_chrome(microsegundos):
    if microsegundos:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(microsegundos / 1000000 - 11644473600))
    return "N/A"

def timestamp_firefox(microsegundos):
    if microsegundos:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(microsegundos / 1000000))
    return "N/A"

def salvar_em_json(dados, navegador, usuario, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    nome_arquivo = output_dir / f"Downloads_{navegador}_{usuario}.json"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"[✓] Arquivo salvo: {nome_arquivo}")

def copiar_banco(origem):
    destino = f"temp_{os.path.basename(origem)}"
    shutil.copy2(origem, destino)
    return destino

def extrair_downloads_chrome_edge(caminho_banco, navegador, usuario, output_dir: Path):
    caminho_temp = copiar_banco(caminho_banco)
    try:
        conn = sqlite3.connect(caminho_temp)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT d.target_path, d.tab_url, d.start_time, d.received_bytes, d.state, u.url
            FROM downloads d
            LEFT JOIN downloads_url_chains u ON d.id = u.id
            ORDER BY d.start_time DESC
            LIMIT 10;
        """)
        rows = cursor.fetchall()

        downloads = []
        for row in rows:
            path, tab_url, start_time, bytes_received, state, source_url = row
            downloads.append({
                "arquivo": path,
                "url_origem": source_url,
                "url_abas": tab_url,
                "inicio_download": timestamp_chrome(start_time),
                "bytes_recebidos": bytes_received,
                "estado": state
            })

        salvar_em_json(downloads, navegador, usuario, output_dir)

    except Exception as e:
        print(f"[!] Erro ({navegador}): {e}")
    finally:
        conn.close()
        os.remove(caminho_temp)

def extrair_downloads_firefox(caminho_banco, usuario, output_dir: Path):
    caminho_temp = copiar_banco(caminho_banco)
    try:
        conn = sqlite3.connect(caminho_temp)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT source, target, startTime, endTime, state
            FROM moz_downloads
            ORDER BY startTime DESC
            LIMIT 10;
        """)
        rows = cursor.fetchall()

        downloads = []
        for row in rows:
            source, target, startTime, endTime, state = row
            downloads.append({
                "arquivo": target,
                "url_origem": source,
                "inicio_download": timestamp_firefox(startTime),
                "estado": state
            })

        salvar_em_json(downloads, "Firefox", usuario, output_dir)

    except Exception as e:
        print(f"[!] Erro (Firefox): {e}")
    finally:
        conn.close()
        os.remove(caminho_temp)

def extract_downloads_history(output_dir: Path, chrome=True, edge=True, firefox=True):
    usuario = os.getlogin()
    home = Path.home()

    if chrome:
        caminho_chrome = home / "AppData/Local/Google/Chrome/User Data/Default/History"
        if caminho_chrome.exists():
            print("[*] Extraindo downloads do Chrome...")
            extrair_downloads_chrome_edge(caminho_chrome, "Chrome", usuario, output_dir)
        else:
            print("[!] Chrome não encontrado.")

    if edge:
        caminho_edge = home / "AppData/Local/Microsoft/Edge/User Data/Default/History"
        if caminho_edge.exists():
            print("[*] Extraindo downloads do Edge...")
            extrair_downloads_chrome_edge(caminho_edge, "Edge", usuario, output_dir)
        else:
            print("[!] Edge não encontrado.")

    if firefox:
        caminho_firefox_perfis = home / "AppData/Roaming/Mozilla/Firefox/Profiles"
        if caminho_firefox_perfis.exists():
            for perfil in caminho_firefox_perfis.iterdir():
                caminho_downloads_sqlite = perfil / "downloads.sqlite"
                if caminho_downloads_sqlite.exists():
                    print(f"[*] Extraindo downloads do Firefox ({perfil.name})...")
                    extrair_downloads_firefox(caminho_downloads_sqlite, usuario, output_dir)
                    break
            else:
                print("[!] downloads.sqlite do Firefox não encontrado.")
        else:
            print("[!] Perfis do Firefox não encontrados.")
