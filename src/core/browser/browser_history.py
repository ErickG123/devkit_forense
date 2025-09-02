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

def save_as_json(dados, navegador, usuario):
    os.makedirs("artefatos/historico", exist_ok=True)
    nome_arquivo = f"artefatos/historico/Historico_{navegador}_{usuario}.json"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"[OK] Histórico salvo: {nome_arquivo}")

def copy_database(origem):
    destino = f"temp_{os.path.basename(origem)}"
    shutil.copy2(origem, destino)
    return destino

def extract_google_edge_history(caminho_banco, navegador, usuario):
    caminho_temp = copy_database(caminho_banco)
    try:
        conn = sqlite3.connect(caminho_temp)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url, title, visit_count, last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC;
        """)
        rows = cursor.fetchall()

        historico_completo = []
        for url, titulo, visitas, ultimo_acesso in rows:
            historico_completo.append({
                "url": url,
                "titulo": titulo,
                "visitas": visitas,
                "ultimo_acesso": timestamp_chrome(ultimo_acesso) if ultimo_acesso else "N/A"
            })

        ultimas_10 = historico_completo[:10]

        cursor.execute("""
            SELECT url, SUM(visit_count) as total_visitas
            FROM urls
            GROUP BY url
            ORDER BY total_visitas DESC
            LIMIT 5;
        """)
        top_5 = [{"url": u, "total_visitas": v} for u, v in cursor.fetchall()]

        dados = {
            "usuario": usuario,
            "navegador": navegador,
            "ultimas_10_urls": ultimas_10,
            "top_5_sites": top_5,
            "historico_completo": historico_completo
        }

        save_as_json(dados, navegador, usuario)

    except Exception as e:
        print(f"[!] Erro ({navegador}): {e}")
    finally:
        conn.close()
        os.remove(caminho_temp)

def extract_firefox_history(caminho_banco, usuario):
    caminho_temp = copy_database(caminho_banco)
    try:
        conn = sqlite3.connect(caminho_temp)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url, title, visit_count, last_visit_date
            FROM moz_places
            ORDER BY last_visit_date DESC;
        """)
        rows = cursor.fetchall()

        historico_completo = []
        for url, titulo, visitas, ultimo_acesso in rows:
            historico_completo.append({
                "url": url,
                "titulo": titulo,
                "visitas": visitas,
                "ultimo_acesso": timestamp_firefox(ultimo_acesso) if ultimo_acesso else "N/A"
            })

        ultimas_10 = historico_completo[:10]

        cursor.execute("""
            SELECT url, SUM(visit_count) as total_visitas
            FROM moz_places
            GROUP BY url
            ORDER BY total_visitas DESC
            LIMIT 5;
        """)
        top_5 = [{"url": u, "total_visitas": v} for u, v in cursor.fetchall()]

        dados = {
            "usuario": usuario,
            "navegador": "Firefox",
            "ultimas_10_urls": ultimas_10,
            "top_5_sites": top_5,
            "historico_completo": historico_completo
        }

        save_as_json(dados, "Firefox", usuario)

    except Exception as e:
        print(f"[!] Erro (Firefox): {e}")
    finally:
        conn.close()
        os.remove(caminho_temp)

def locale_database():
    usuario = os.getlogin()
    home = str(Path.home())

    caminho_chrome = os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History")
    if os.path.exists(caminho_chrome):
        print("[*] Extraindo histórico do Chrome...")
        extract_google_edge_history(caminho_chrome, "Chrome", usuario)
    else:
        print("[!] Chrome não encontrado.")

    caminho_edge = os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History")
    if os.path.exists(caminho_edge):
        print("[*] Extraindo histórico do Edge...")
        extract_google_edge_history(caminho_edge, "Edge", usuario)
    else:
        print("[!] Edge não encontrado.")

    caminho_firefox_perfis = os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
    if os.path.exists(caminho_firefox_perfis):
        for perfil in os.listdir(caminho_firefox_perfis):
            caminho_sqlite = os.path.join(caminho_firefox_perfis, perfil, "places.sqlite")
            if os.path.exists(caminho_sqlite):
                print(f"[*] Extraindo histórico do Firefox ({perfil})...")
                extract_firefox_history(caminho_sqlite, usuario)
                break
        else:
            print("[!] places.sqlite do Firefox não encontrado.")
    else:
        print("[!] Perfis do Firefox não encontrados.")

if __name__ == "__main__":
    locale_database()
