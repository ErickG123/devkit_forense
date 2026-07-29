import os
import zipfile

dist_root = os.path.join('dist', 'forenselab-ui')
dist_browser = os.path.join(dist_root, 'browser')
# Suporte para Angular 17+ (pasta browser) ou versões anteriores
source_path = dist_browser if os.path.exists(dist_browser) else dist_root

if not os.path.exists(source_path):
    print(f"Erro: Pasta {source_path} não encontrada.")
    exit(1)

zip_filename = 'gh-pages.zip'

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    for root, dirs, files in os.walk(source_path):
        for file in files:
            file_path = os.path.join(root, file)
            # Cria a estrutura exata que o GitHub Pages/Releases gera
            arcname = os.path.join('devkit_forense-gh-pages', os.path.relpath(file_path, source_path))
            # Garante barras normais no zip (padrão universal)
            zip_file.write(file_path, arcname.replace('\\', '/'))

print(f"Zip concluído com sucesso: {zip_filename}")
