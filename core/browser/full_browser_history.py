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
    os.makedirs("artefatos/historico", exist_ok=True)
    nome_arquivo = f"artefatos/historico/Historico_{navegador}_{usuario}.json"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"[OK] Histórico salvo: {nome_arquivo}")

def copiar_banco(origem):
    destino = f"temp_{os.path.basename(origem)}"
    shutil.copy2(origem, destino)
    return destino

def extrair_historico_chrome_edge(caminho_banco, navegador, usuario):
    caminho_temp = copiar_banco(caminho_banco)
    try:
        conn = sqlite3.connect(caminho_temp)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url, title, visit_count, last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC;
        """)
        rows = cursor.fetchall()

        historico = []
        for row in rows:
            url, titulo, visitas, ultimo_acesso = row
            historico.append({
                "url": url,
                "titulo": titulo,
                "visitas": visitas,
                "ultimo_acesso": timestamp_chrome(ultimo_acesso) if ultimo_acesso else "N/A"
            })

        salvar_em_json(historico, navegador, usuario)

    except Exception as e:
        print(f"[!] Erro ({navegador}): {e}")
    finally:
        conn.close()
        os.remove(caminho_temp)

def extrair_historico_firefox(caminho_banco, usuario):
    caminho_temp = copiar_banco(caminho_banco)
    try:
        conn = sqlite3.connect(caminho_temp)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url, title, visit_count, last_visit_date
            FROM moz_places
            ORDER BY last_visit_date DESC;
        """)
        rows = cursor.fetchall()

        historico = []
        for row in rows:
            url, titulo, visitas, ultimo_acesso = row
            historico.append({
                "url": url,
                "titulo": titulo,
                "visitas": visitas,
                "ultimo_acesso": timestamp_firefox(ultimo_acesso) if ultimo_acesso else "N/A"
            })

        salvar_em_json(historico, "Firefox", usuario)

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
        print("[*] Extraindo histórico do Chrome...")
        extrair_historico_chrome_edge(caminho_chrome, "Chrome", usuario)
    else:
        print("[!] Chrome não encontrado.")

    # Edge
    caminho_edge = os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History")
    if os.path.exists(caminho_edge):
        print("[*] Extraindo histórico do Edge...")
        extrair_historico_chrome_edge(caminho_edge, "Edge", usuario)
    else:
        print("[!] Edge não encontrado.")

    # Firefox
    caminho_firefox_perfis = os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
    if os.path.exists(caminho_firefox_perfis):
        for perfil in os.listdir(caminho_firefox_perfis):
            caminho_sqlite = os.path.join(caminho_firefox_perfis, perfil, "places.sqlite")
            if os.path.exists(caminho_sqlite):
                print(f"[*] Extraindo histórico do Firefox ({perfil})...")
                extrair_historico_firefox(caminho_sqlite, usuario)
                break
        else:
            print("[!] places.sqlite do Firefox não encontrado.")
    else:
        print("[!] Perfis do Firefox não encontrados.")

if __name__ == "__main__":
    localizar_bancos_e_extrair()
