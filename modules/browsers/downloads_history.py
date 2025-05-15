import os
import sqlite3
import time
import json
import shutil
from pathlib import Path

def timestamp_chrome(microsegundos):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(microsegundos / 1000000 - 11644473600))

def timestamp_firefox(microsegundos):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(microsegundos / 1000000))

def salvar_em_json(dados, navegador, usuario):
    os.makedirs("artefatos/downloads", exist_ok=True)
    nome_arquivo = f"artefatos/downloads/Downloads_{navegador}_{usuario}.json"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"[✓] Arquivo salvo: {nome_arquivo}")

def copiar_banco(origem):
    destino = f"temp_{os.path.basename(origem)}"
    shutil.copy2(origem, destino)
    return destino

def extrair_downloads_chrome_edge(caminho_banco, navegador, usuario):
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

        salvar_em_json(downloads, navegador, usuario)

    except Exception as e:
        print(f"[!] Erro ({navegador}): {e}")
    finally:
        conn.close()
        os.remove(caminho_temp)

def extrair_downloads_firefox(caminho_banco, usuario):
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

        salvar_em_json(downloads, "Firefox", usuario)

    except Exception as e:
        print(f"[!] Erro (Firefox): {e}")
    finally:
        conn.close()
        os.remove(caminho_temp)

def localizar_bancos_e_extrair():
    usuario = os.getlogin()
    home = str(Path.home())

    # Chrome
    caminho_chrome = os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History")
    if os.path.exists(caminho_chrome):
        print("[*] Extraindo downloads do Chrome...")
        extrair_downloads_chrome_edge(caminho_chrome, "Chrome", usuario)
    else:
        print("[!] Chrome não encontrado.")

    # Edge
    caminho_edge = os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History")
    if os.path.exists(caminho_edge):
        print("[*] Extraindo downloads do Edge...")
        extrair_downloads_chrome_edge(caminho_edge, "Edge", usuario)
    else:
        print("[!] Edge não encontrado.")

    # Firefox
    caminho_firefox_perfis = os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
    if os.path.exists(caminho_firefox_perfis):
        for perfil in os.listdir(caminho_firefox_perfis):
            caminho_downloads_sqlite = os.path.join(caminho_firefox_perfis, perfil, "downloads.sqlite")
            if os.path.exists(caminho_downloads_sqlite):
                print(f"[*] Extraindo downloads do Firefox ({perfil})...")
                extrair_downloads_firefox(caminho_downloads_sqlite, usuario)
                break
        else:
            print("[!] downloads.sqlite do Firefox não encontrado.")
    else:
        print("[!] Perfis do Firefox não encontrados.")

if __name__ == "__main__":
    localizar_bancos_e_extrair()
