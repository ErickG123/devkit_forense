import sqlite3
from collections import Counter
import re

caminho_banco = r'C:\Users\Usuário\AppData\Local\Google\Chrome\User Data\Default\History'

conn = sqlite3.connect(caminho_banco)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = [t[0] for t in cursor.fetchall()]

termos_pesquisa = []

if 'keyword_search_terms' in tabelas:
    cursor.execute("SELECT term FROM keyword_search_terms")
    termos = cursor.fetchall()
    termos_pesquisa = [t[0] for t in termos]
else:
    print("Tabela 'keyword_search_terms' não encontrada. Usando fallback por URL...")
    cursor.execute("SELECT url FROM urls")
    urls = cursor.fetchall()

    for (url,) in urls:
        match = re.search(r"[?&]q=([^&]+)", url)
        if match:
            termo = match.group(1)
            termos_pesquisa.append(termo)

conn.close()

todas_palavras = []
for termo in termos_pesquisa:
    palavras = re.findall(r'\b\w+\b', termo.lower())
    todas_palavras.extend(palavras)

contagem = Counter(todas_palavras)

print("\nPalavras mais pesquisadas:")
for palavra, freq in contagem.most_common(20):
    print(f"{palavra}: {freq}")
