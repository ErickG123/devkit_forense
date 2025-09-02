from pathlib import Path

def generate_index():
    docs_dir = Path("docs")
    changelog_dir = docs_dir / "changelog"
    changelog_files = sorted(changelog_dir.glob("*.md"), reverse=True)

    html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Forensic CLI Documentation & Changelog</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 2rem auto; line-height: 1.6; padding: 0 1rem; }
        h1, h2 { color: #333; }
        a { text-decoration: none; color: #1a73e8; }
        a:hover { text-decoration: underline; }
        ul { list-style-type: none; padding-left: 0; }
        li { margin-bottom: 0.5rem; }
        .section { margin-top: 2rem; }
    </style>
</head>
<body>
    <h1>Forensic CLI</h1>
    <p>Bem-vindo à documentação do Forensic CLI! Abaixo você encontra links para o changelog e a documentação.</p>

    <div class="section">
        <h2>Documentação</h2>
        <ul>
            <li><a href="index.html">Página principal da documentação</a></li>
        </ul>
    </div>

    <div class="section">
        <h2>Changelog</h2>
        <ul>
"""

    for file in changelog_files:
        tag_name = file.stem
        html_content += f'            <li><a href="changelog/{file.name}">{tag_name}</a></li>\n'

    html_content += """        </ul>
    </div>

    <div class="section">
        <h2>Source Code</h2>
        <ul>
            <li><a href="https://github.com/seu-usuario/forensic-cli">Repositório no GitHub</a></li>
        </ul>
    </div>

</body>
</html>
"""

    index_path = docs_dir / "index.html"
    index_path.write_text(html_content, encoding="utf-8")
    print(f"index.html gerado com {len(changelog_files)} links de changelog.")

if __name__ == "__main__":
    generate_index()
