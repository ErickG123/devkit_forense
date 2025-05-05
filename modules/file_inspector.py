import os
import hashlib
import csv
import time
import re
from datetime import datetime
from collections import defaultdict

def gerar_hash(file_path):
    """ Gera o hash SHA256 de um arquivo """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Ler o arquivo em pedaços de 4k para não sobrecarregar a memória
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verificar_extensao_dupla(file_name):
    """ Verifica se um arquivo possui extensão dupla (ex: .jpg.exe) """
    return bool(re.search(r"\.[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)$", file_name))

def inspecionar_diretorio(diretorio):
    """ Inspeciona o diretório e gera um relatório forense """
    arquivos_info = []
    hashes = defaultdict(list)

    for root, dirs, files in os.walk(diretorio):
        for file in files:
            file_path = os.path.join(root, file)
            tamanho = os.path.getsize(file_path)
            modificado_em = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            criado_em = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            hash_sha256 = gerar_hash(file_path)

            arquivos_info.append({
                "caminho": file_path,
                "tamanho_bytes": tamanho,
                "modificado_em": modificado_em,
                "criado_em": criado_em,
                "hash_sha256": hash_sha256
            })

            hashes[hash_sha256].append(file_path)

    return arquivos_info, hashes

def gerar_relatorio_csv(arquivos_info, nome_arquivo="relatorio_forense.csv"):
    """ Gera um relatório CSV com os arquivos analisados """
    with open(nome_arquivo, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["caminho", "tamanho_bytes", "modificado_em", "criado_em", "hash_sha256"])
        writer.writeheader()
        for file_info in arquivos_info:
            writer.writerow(file_info)
    print(f"Relatório CSV gerado: {nome_arquivo}")

def gerar_relatorio_html(arquivos_info, nome_arquivo="relatorio_forense.html"):
    """ Gera um relatório HTML com os arquivos analisados """
    with open(nome_arquivo, mode="w") as file:
        file.write("<html><head><title>Relatório Forense</title></head><body>")
        file.write("<h1>Relatório Forense de Arquivos</h1>")
        file.write("<table border='1'><tr><th>Caminho</th><th>Tamanho (bytes)</th><th>Modificado em</th><th>Criado em</th><th>Hash SHA256</th></tr>")
        for file_info in arquivos_info:
            file.write(f"<tr><td>{file_info['caminho']}</td><td>{file_info['tamanho_bytes']}</td><td>{file_info['modificado_em']}</td><td>{file_info['criado_em']}</td><td>{file_info['hash_sha256']}</td></tr>")
        file.write("</table></body></html>")
    print(f"Relatório HTML gerado: {nome_arquivo}")

def exibir_arquivos_duplicados(hashes):
    """ Exibe arquivos duplicados com base no hash """
    for hash_value, paths in hashes.items():
        if len(paths) > 1:
            print(f"\nArquivos duplicados com hash {hash_value}:")
            for path in paths:
                print(f"  - {path}")

def exibir_extensao_dupla(arquivos_info):
    """ Exibe arquivos com extensão dupla """
    for file_info in arquivos_info:
        if verificar_extensao_dupla(file_info['caminho']):
            print(f"Arquivo suspeito de extensão dupla: {file_info['caminho']}")

# Exemplo de uso
diretorio = "amostras_forenses"  # Substitua pelo caminho do seu diretório
arquivos_info, hashes = inspecionar_diretorio(diretorio)

# Gerar relatórios
gerar_relatorio_csv(arquivos_info)
gerar_relatorio_html(arquivos_info)

# Exibir arquivos duplicados e suspeitos
exibir_arquivos_duplicados(hashes)
exibir_extensao_dupla(arquivos_info)
