import os
import sqlite3
import shutil
import json
import time

def recuperar_historico(chrome=False, firefox=False, edge=False, usuario="Usuário Anônimo"):
    print(f"Recuperando o histórico para o usuário: {usuario}...")

    if chrome:
        print("Recuperando histórico do Google Chrome...")
        recuperar_historico_chrome(usuario)
    elif firefox:
        print("Recuperando histórico do Mozilla Firefox...")
        recuperar_historico_firefox(usuario)
    elif edge:
        print("Recuperando histórico do Microsoft Edge...")
        recuperar_historico_edge(usuario)
    else:
        print("Nenhum navegador especificado.")

def copiar_banco_de_dados(caminho_origem, nome_arquivo, usuario):
    caminho_destino = os.path.expanduser(f"~\\Desktop\\Históricos\\{usuario}")
    
    if not os.path.exists(caminho_destino):
        os.makedirs(caminho_destino)

    try:
        shutil.copy(caminho_origem, os.path.join(caminho_destino, nome_arquivo))
        print(f"Histórico copiado com sucesso para {os.path.join(caminho_destino, nome_arquivo)}")
    except Exception as e:
        print(f"Erro ao copiar o banco de dados: {e}")

def recuperar_historico_chrome(usuario):
    # Caminho do banco de dados de histórico do Google Chrome
    caminho_banco_chrome = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\History"

    if os.path.exists(caminho_banco_chrome):
        # Copiando o banco de dados do Chrome
        copiar_banco_de_dados(caminho_banco_chrome, "History_Chrome", usuario)

        try:
            conn = sqlite3.connect(caminho_banco_chrome)
            cursor = conn.cursor()

            # Consultando as últimas 10 URLs visitadas
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 10;")
            rows_ultimas = cursor.fetchall()

            # Consultando os Top 5 sites mais acessados
            cursor.execute("SELECT url, SUM(visit_count) as total_visitas FROM urls GROUP BY url ORDER BY total_visitas DESC LIMIT 5;")
            rows_top5 = cursor.fetchall()

            # Exibindo as últimas 10 URLs acessadas
            print(f"10 Últimas URLs acessadas no Google Chrome para o usuário {usuario}:")
            for row in rows_ultimas:
                url, title, visit_count, last_visit_time = row
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_visit_time / 1000000 - 11644473600))
                print(f"URL: {url}\nTítulo: {title}\nVisitas: {visit_count}\nÚltima Visita: {timestamp}\n")

            # Exibindo os 5 sites mais acessados
            print(f"\nTop 5 sites mais acessados no Google Chrome para o usuário {usuario}:")
            for row in rows_top5:
                url, total_visitas = row
                print(f"URL: {url}\nTotal de Visitas: {total_visitas}\n")
        except Exception as e:
            print(f"Erro ao acessar o banco de dados do Chrome: {e}")
        finally:
            conn.close()
    else:
        print(f"O banco de dados do Chrome não foi encontrado. Verifique o caminho.")

def recuperar_historico_firefox(usuario):
    # Caminho do banco de dados de histórico do Mozilla Firefox
    caminho_banco_firefox = os.path.expanduser("~") + r"\AppData\Roaming\Mozilla\Firefox\Profiles"
    
    if os.path.exists(caminho_banco_firefox):
        for perfil in os.listdir(caminho_banco_firefox):
            caminho_perfil = os.path.join(caminho_banco_firefox, perfil, "places.sqlite")
            if os.path.exists(caminho_perfil):
                # Copiando o banco de dados do Firefox
                copiar_banco_de_dados(caminho_perfil, "places_Firefox", usuario)

                try:
                    conn = sqlite3.connect(caminho_perfil)
                    cursor = conn.cursor()

                    # Consultando as últimas 10 URLs visitadas
                    cursor.execute("SELECT url, title, visit_count, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 10;")
                    rows_ultimas = cursor.fetchall()

                    # Consultando os Top 5 sites mais acessados
                    cursor.execute("SELECT url, SUM(visit_count) as total_visitas FROM moz_places GROUP BY url ORDER BY total_visitas DESC LIMIT 5;")
                    rows_top5 = cursor.fetchall()

                    # Exibindo as últimas 10 URLs acessadas
                    print(f"10 Últimas URLs acessadas no Mozilla Firefox para o usuário {usuario}:")
                    for row in rows_ultimas:
                        url, title, visit_count, last_visit_time = row
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_visit_time / 1000000))
                        print(f"URL: {url}\nTítulo: {title}\nVisitas: {visit_count}\nÚltima Visita: {timestamp}\n")

                    # Exibindo os 5 sites mais acessados
                    print(f"\nTop 5 sites mais acessados no Mozilla Firefox para o usuário {usuario}:")
                    for row in rows_top5:
                        url, total_visitas = row
                        print(f"URL: {url}\nTotal de Visitas: {total_visitas}\n")
                except Exception as e:
                    print(f"Erro ao acessar o banco de dados do Firefox: {e}")
                finally:
                    conn.close()
                break
        else:
            print(f"Perfil do Firefox não encontrado.")
    else:
        print(f"O diretório de perfis do Firefox não foi encontrado.")

def recuperar_historico_edge(usuario):
    # Caminho do banco de dados de histórico do Microsoft Edge
    caminho_banco_edge = os.path.expanduser("~") + r"\AppData\Local\Microsoft\Edge\User Data\Default\History"
    
    if os.path.exists(caminho_banco_edge):
        # Copiando o banco de dados do Edge
        copiar_banco_de_dados(caminho_banco_edge, "History_Edge", usuario)

        try:
            conn = sqlite3.connect(caminho_banco_edge)
            cursor = conn.cursor()

            # Consultando as últimas 10 URLs visitadas
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 10;")
            rows_ultimas = cursor.fetchall()

            # Consultando os Top 5 sites mais acessados
            cursor.execute("SELECT url, SUM(visit_count) as total_visitas FROM urls GROUP BY url ORDER BY total_visitas DESC LIMIT 5;")
            rows_top5 = cursor.fetchall()

            # Exibindo as últimas 10 URLs acessadas
            print(f"10 Últimas URLs acessadas no Microsoft Edge para o usuário {usuario}:")
            for row in rows_ultimas:
                url, title, visit_count, last_visit_time = row
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_visit_time / 1000000 - 11644473600))
                print(f"URL: {url}\nTítulo: {title}\nVisitas: {visit_count}\nÚltima Visita: {timestamp}\n")

            # Exibindo os 5 sites mais acessados
            print(f"\nTop 5 sites mais acessados no Microsoft Edge para o usuário {usuario}:")
            for row in rows_top5:
                url, total_visitas = row
                print(f"URL: {url}\nTotal de Visitas: {total_visitas}\n")
        except Exception as e:
            print(f"Erro ao acessar o banco de dados do Edge: {e}")
        finally:
            conn.close()
    else:
        print(f"O banco de dados do Edge não foi encontrado. Verifique o caminho.")
