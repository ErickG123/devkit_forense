from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
import hashlib
import requests
import json
import time

def carregar_json(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)

def extrair_urls_validas(dados_json):
    urls = []

    for chave in ["historico_ultimas_urls", "ultimas_10_urls", "historico_completo"]:
        entradas = dados_json.get(chave, [])
        for entrada in entradas:
            url = entrada.get("url")
            if url and url.startswith("http"):
                urls.append(url)

    return urls

def baixar_favicon(url, pasta_destino: Path):
    try:
        pasta_destino.mkdir(parents=True, exist_ok=True)
        dominio = urlparse(url).netloc
        favicon_url = f"https://{dominio}/favicon.ico"
        resposta = requests.get(favicon_url, timeout=5)
        if resposta.status_code == 200:
            nome_arquivo = hashlib.md5(dominio.encode()).hexdigest() + ".ico"
            caminho = pasta_destino / nome_arquivo
            with open(caminho, "wb") as f:
                f.write(resposta.content)
            print(f"[FAVICON] Baixado: {dominio}")
        else:
            print(f"[FAVICON] Não encontrado para {dominio}")
    except Exception as e:
        print(f"[FAVICON] Erro ao baixar de {url}: {e}")

def capturar_print(url, pasta_destino: Path):
    try:
        pasta_destino.mkdir(parents=True, exist_ok=True)
        nome_arquivo = hashlib.md5(url.encode()).hexdigest() + ".png"
        caminho = pasta_destino / nome_arquivo

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,1024")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(10)
        driver.get(url)
        time.sleep(3)
        driver.save_screenshot(str(caminho))
        driver.quit()
        print(f"[PRINT] Capturado: {url}")
    except Exception as e:
        print(f"[PRINT] Erro ao capturar print de {url}: {e}")

def processar_urls(urls, output_dir: Path):
    fav_dir = output_dir / "favicons"
    print_dir = output_dir / "prints"
    for url in urls:
        print(f"\n[PROCESSANDO] {url}")
        baixar_favicon(url, fav_dir)
        capturar_print(url, print_dir)
