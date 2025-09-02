# core/browser/words_extractor.py
import sqlite3
import shutil
import tempfile
import re
from collections import Counter
from urllib.parse import unquote
from pathlib import Path
import json
import typer

def extract_words(chrome: bool = True, output_dir: Path = Path("artefatos/words_output")):
    termos_pesquisa = []

    if chrome:
        chrome_history_path = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/History"
        if not chrome_history_path.exists():
            typer.echo("[!] Histórico do Chrome não encontrado.")
            return

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        shutil.copy2(chrome_history_path, tmp_file.name)

        conn = sqlite3.connect(tmp_file.name)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [t[0] for t in cursor.fetchall()]

        if 'keyword_search_terms' in tabelas:
            cursor.execute("SELECT term FROM keyword_search_terms")
            termos = cursor.fetchall()
            termos_pesquisa = [t[0] for t in termos]
        else:
            typer.echo("Tabela 'keyword_search_terms' não encontrada. Usando fallback por URL...")
            cursor.execute("SELECT url FROM urls")
            urls = cursor.fetchall()
            for (url,) in urls:
                match = re.search(r"[?&]q=([^&]+)", url)
                if match:
                    termo = unquote(match.group(1))
                    termos_pesquisa.append(termo)

        conn.close()
        tmp_file.close()

    todas_palavras = []
    for termo in termos_pesquisa:
        palavras = re.findall(r'\b\w+\b', termo.lower())
        todas_palavras.extend(palavras)

    contagem = Counter(todas_palavras)
    palavras_mais_comuns = contagem.most_common(50)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "most_searched_words.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(palavras_mais_comuns, f, indent=2, ensure_ascii=False)

    typer.echo(f"✅ Palavras mais pesquisadas salvas em: {output_file}")
