import os
import sqlite3
import shutil
import time
import json

def copiar_banco_de_dados(caminho_origem, nome_arquivo, usuario):
    caminho_destino = os.path.expanduser(f"~\\Desktop\\Históricos\\{usuario}")
    if not os.path.exists(caminho_destino):
        os.makedirs(caminho_destino)

    try:
        shutil.copy(caminho_origem, os.path.join(caminho_destino, nome_arquivo))
        print(f"Histórico copiado com sucesso para {os.path.join(caminho_destino, nome_arquivo)}")
    except Exception as e:
        print(f"Erro ao copiar o banco de dados: {e}")

def salvar_historico_em_json(dados, nome_arquivo):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"Histórico salvo em {nome_arquivo}")

def recuperar_historico_chrome(usuario):
    print(f"Tentando acessar o histórico do Chrome para o usuário {usuario}...")
    caminho_banco_chrome = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\History"

    if os.path.exists(caminho_banco_chrome):
        print(f"Banco de dados do Chrome encontrado em: {caminho_banco_chrome}")
        copiar_banco_de_dados(caminho_banco_chrome, "History_Chrome", usuario)

        try:
            conn = sqlite3.connect(caminho_banco_chrome)
            cursor = conn.cursor()
            print("Conexão bem-sucedida ao banco de dados do Chrome.")

            # Consultando as últimas 10 URLs visitadas
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 10;")
            rows_ultimas = cursor.fetchall()
            if not rows_ultimas:
                print("Nenhuma URL encontrada no histórico do Chrome.")

            # Consultando os Top 5 sites mais acessados
            cursor.execute("SELECT url, SUM(visit_count) as total_visitas FROM urls GROUP BY url ORDER BY total_visitas DESC LIMIT 5;")
            rows_top5 = cursor.fetchall()
            if not rows_top5:
                print("Nenhum site encontrado no Top 5 do Chrome.")

            historico = {
                "usuario": usuario,
                "historico_ultimas_urls": [],
                "top_5_sites": []
            }

            # Adicionando as últimas 10 URLs acessadas
            for row in rows_ultimas:
                url, title, visit_count, last_visit_time = row
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_visit_time / 1000000 - 11644473600))
                historico["historico_ultimas_urls"].append({
                    "url": url,
                    "title": title,
                    "visit_count": visit_count,
                    "last_visit_time": timestamp
                })

            # Adicionando os 5 sites mais acessados
            for row in rows_top5:
                url, total_visitas = row
                historico["top_5_sites"].append({
                    "url": url,
                    "total_visitas": total_visitas
                })

            # Salvando o histórico em JSON
            salvar_historico_em_json(historico, f"{usuario}_historico_chrome.json")

        except Exception as e:
            print(f"Erro ao acessar o banco de dados do Chrome: {e}")
        finally:
            conn.close()
    else:
        print(f"O banco de dados do Chrome não foi encontrado. Verifique o caminho.")

def recuperar_historico_firefox(usuario):
    print(f"Tentando acessar o histórico do Firefox para o usuário {usuario}...")
    caminho_perfil_firefox = os.path.expanduser("~") + r"\AppData\Roaming\Mozilla\Firefox\Profiles"

    # Encontrar o perfil do Firefox
    for pasta in os.listdir(caminho_perfil_firefox):
        caminho_perfil = os.path.join(caminho_perfil_firefox, pasta)
        if os.path.isdir(caminho_perfil):
            caminho_banco_firefox = os.path.join(caminho_perfil, "places.sqlite")
            if os.path.exists(caminho_banco_firefox):
                print(f"Banco de dados do Firefox encontrado em: {caminho_banco_firefox}")
                copiar_banco_de_dados(caminho_banco_firefox, "places.sqlite_Firefox", usuario)

                try:
                    conn = sqlite3.connect(caminho_banco_firefox)
                    cursor = conn.cursor()
                    print("Conexão bem-sucedida ao banco de dados do Firefox.")

                    # Consultando as últimas 10 URLs visitadas
                    cursor.execute("SELECT url, title, visit_count, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 10;")
                    rows_ultimas = cursor.fetchall()
                    if not rows_ultimas:
                        print("Nenhuma URL encontrada no histórico do Firefox.")

                    historico = {
                        "usuario": usuario,
                        "historico_ultimas_urls": []
                    }

                    # Adicionando as últimas 10 URLs acessadas
                    for row in rows_ultimas:
                        url, title, visit_count, last_visit_date = row
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(last_visit_date / 1000000))
                        historico["historico_ultimas_urls"].append({
                            "url": url,
                            "title": title,
                            "visit_count": visit_count,
                            "last_visit_date": timestamp
                        })

                    # Salvando o histórico em JSON
                    salvar_historico_em_json(historico, f"{usuario}_historico_firefox.json")

                except Exception as e:
                    print(f"Erro ao acessar o banco de dados do Firefox: {e}")
                finally:
                    conn.close()
            else:
                print(f"O banco de dados do Firefox não foi encontrado no perfil {pasta}.")
        else:
            print(f"Não é um diretório válido: {pasta}")

def recuperar_historico_edge(usuario):
    print(f"Tentando acessar o histórico do Edge para o usuário {usuario}...")
    caminho_banco_edge = os.path.expanduser("~") + r"\AppData\Local\Microsoft\Edge\User Data\Default\History"

    if os.path.exists(caminho_banco_edge):
        print(f"Banco de dados do Edge encontrado em: {caminho_banco_edge}")
        copiar_banco_de_dados(caminho_banco_edge, "History_Edge", usuario)

        try:
            conn = sqlite3.connect(caminho_banco_edge)
            cursor = conn.cursor()
            print("Conexão bem-sucedida ao banco de dados do Edge.")

            # Consultando as últimas 10 URLs visitadas
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 10;")
            rows_ultimas = cursor.fetchall()
            if not rows_ultimas:
                print("Nenhuma URL encontrada no histórico do Edge.")

            # Consultando os Top 5 sites mais acessados
            cursor.execute("SELECT url, SUM(visit_count) as total_visitas FROM urls GROUP BY url ORDER BY total_visitas DESC LIMIT 5;")
            rows_top5 = cursor.fetchall()
            if not rows_top5:
                print("Nenhum site encontrado no Top 5 do Edge.")

            historico = {
                "usuario": usuario,
                "historico_ultimas_urls": [],
                "top_5_sites": []
            }

            # Adicionando as últimas 10 URLs acessadas
            for row in rows_ultimas:
                url, title, visit_count, last_visit_time = row
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_visit_time / 1000000 - 11644473600))
                historico["historico_ultimas_urls"].append({
                    "url": url,
                    "title": title,
                    "visit_count": visit_count,
                    "last_visit_time": timestamp
                })

            # Adicionando os 5 sites mais acessados
            for row in rows_top5:
                url, total_visitas = row
                historico["top_5_sites"].append({
                    "url": url,
                    "total_visitas": total_visitas
                })

            # Salvando o histórico em JSON
            salvar_historico_em_json(historico, f"{usuario}_historico_edge.json")

        except Exception as e:
            print(f"Erro ao acessar o banco de dados do Edge: {e}")
        finally:
            conn.close()
    else:
        print(f"O banco de dados do Edge não foi encontrado. Verifique o caminho.")

# Exemplo de uso
usuario = os.getlogin()
recuperar_historico_chrome(usuario)
recuperar_historico_edge(usuario)
# recuperar_historico_firefox(usuario)
