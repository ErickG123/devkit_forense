import os
import zipfile

# Nome da pasta e do ZIP
base_dir = "amostras_forenses"
zip_path = "amostras_forenses.zip"

# Conteúdos simulados
arquivos = {
    "documento_legitimo.pdf": "Este é um arquivo PDF legítimo.",
    "foto.jpg": b"\xff\xd8\xff\xe0" + "JPEG conteúdo simulado".encode("utf-8"),
    "foto.jpg.exe": "Executável disfarçado de imagem.",
    "relatorio.docx": "Relatório original",
    "relatorio_copia.docx": "Relatório original",
    "planilha.xls.scr": "Arquivo renomeado para enganar",
    "vazio.txt": b"",
}

# Criar pasta se não existir
os.makedirs(base_dir, exist_ok=True)

# Criar arquivos na pasta
for nome, conteudo in arquivos.items():
    caminho = os.path.join(base_dir, nome)
    with open(caminho, "wb") as f:
        if isinstance(conteudo, str):
            conteudo = conteudo.encode("utf-8")
        f.write(conteudo)

# Compactar em ZIP
with zipfile.ZipFile(zip_path, "w") as zipf:
    for root, _, files in os.walk(base_dir):
        for file in files:
            full_path = os.path.join(root, file)
            arcname = os.path.relpath(full_path, base_dir)
            zipf.write(full_path, arcname=os.path.join(base_dir, arcname))

print(f"Arquivos gerados e compactados com sucesso em: {zip_path}")
