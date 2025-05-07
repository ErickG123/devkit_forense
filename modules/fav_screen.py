import os
import json
import requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
from io import BytesIO
import hashlib
import time

# Criação de pastas
os.makedirs("artefatos/favicons", exist_ok=True)
os.makedirs("artefatos/prints", exist_ok=True)

# Carregar JSONs de histórico
def carregar_json(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)

# Extrair URLs válidas de um histórico
def extrair_urls_validas(dados_json):
    urls = []
    for entrada in dados_json:
        url = entrada.get("url")
        if url and url.startswith("http"):
            urls.append(url)
    return urls

# Download do favicon
def baixar_favicon(url, pasta_destino="artefatos/favicons"):
    try:
        dominio = urlparse(url).netloc
        favicon_url = f"https://{dominio}/favicon.ico"
        resposta = requests.get(favicon_url, timeout=5)
        if resposta.status_code == 200:
            nome_arquivo = hashlib.md5(dominio.encode()).hexdigest() + ".ico"
            caminho = os.path.join(pasta_destino, nome_arquivo)
            with open(caminho, "wb") as f:
                f.write(resposta.content)
            print(f"[FAVICON] Baixado: {dominio}")
        else:
            print(f"[FAVICON] Não encontrado para {dominio}")
    except Exception as e:
        print(f"[FAVICON] Erro ao baixar de {url}: {e}")

# Captura de print com Selenium
def capturar_print(url, pasta_destino="artefatos/prints"):
    try:
        nome_arquivo = hashlib.md5(url.encode()).hexdigest() + ".png"
        caminho = os.path.join(pasta_destino, nome_arquivo)

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,1024")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(10)
        driver.get(url)
        time.sleep(3)  # esperar renderizar
        driver.save_screenshot(caminho)
        driver.quit()
        print(f"[PRINT] Capturado: {url}")
    except Exception as e:
        print(f"[PRINT] Erro ao capturar print de {url}: {e}")

# Processar lista de URLs
def processar_urls(urls):
    for url in urls:
        print(f"\n[PROCESSANDO] {url}")
        baixar_favicon(url)
        capturar_print(url)

# Main
if __name__ == "__main__":
    try:
        pasta_jsons = "artefatos/historico"
        arquivos_json = [os.path.join(pasta_jsons, arquivo) for arquivo in os.listdir(pasta_jsons) if arquivo.endswith(".json")]
        todas_urls = []

        for caminho in arquivos_json:
            if os.path.exists(caminho):
                print(f"[INFO] Carregando: {caminho}")
                dados = carregar_json(caminho)
                urls = extrair_urls_validas(dados)
                todas_urls.extend(urls)
            else:
                print(f"[AVISO] Arquivo não encontrado: {caminho}")

        if todas_urls:
            todas_urls = list(set(todas_urls))  # remove duplicadas
            processar_urls(todas_urls)
            print("\n✅ Processamento finalizado.")
        else:
            print("\n⚠️ Nenhum arquivo JSON válido encontrado ou sem URLs úteis.")

    except Exception as erro:
        print(f"\n❌ Erro geral: {erro}")
