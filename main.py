# -*- coding: utf-8 -*-
import sys
import io
import argparse
# from modules.file_inspector import (
#     inspecionar_diretorio,
#     gerar_relatorio_csv,
#     gerar_relatorio_html,
#     exibir_arquivos_duplicados,
#     exibir_extensao_dupla
# )
from modules.browsers.browser_history import (
    recuperar_historico_chrome,
    recuperar_historico_edge,
    recuperar_historico_firefox
)
from modules.browsers.unusual_patterns import processar_historico_da_pasta

# Força UTF-8 no terminal (Windows-safe)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description="DevKit Forense - Análise de Arquivos e Navegadores")

    # 📁 Análise de arquivos
    parser.add_argument("diretorio", nargs="?", default=None, help="Diretório a ser analisado")
    parser.add_argument("--csv", action="store_true", help="Gerar relatório CSV dos arquivos")
    parser.add_argument("--html", action="store_true", help="Gerar relatório HTML dos arquivos")
    parser.add_argument("--duplicados", action="store_true", help="Exibir arquivos duplicados")
    parser.add_argument("--extensao-dupla", action="store_true", help="Exibir arquivos com extensão dupla")

    # 🌐 Histórico dos navegadores
    parser.add_argument("--chrome", action="store_true", help="Analisar histórico do Google Chrome")
    parser.add_argument("--firefox", action="store_true", help="Analisar histórico do Mozilla Firefox")
    parser.add_argument("--edge", action="store_true", help="Analisar histórico do Microsoft Edge")

    # 🔍 Padrões incomuns de acesso
    parser.add_argument("--analisar-padroes", action="store_true", help="Detectar padrões incomuns de acesso na pasta 'artefatos/historico'")

    # Personalização
    parser.add_argument("--usuario", type=str, default="Usuário Anônimo", help="Nome do usuário para personalização")

    args = parser.parse_args()
    print(f"\n🔍 Olá, {args.usuario}! Iniciando a análise...\n")

    # 📁 Análise de arquivos
    # if args.diretorio:
    #     arquivos_info, hashes = inspecionar_diretorio(args.diretorio)

    #     if args.csv:
    #         gerar_relatorio_csv(arquivos_info)
    #     if args.html:
    #         gerar_relatorio_html(arquivos_info)
    #     if args.duplicados:
    #         exibir_arquivos_duplicados(hashes)
    #     if args.extensao_dupla:
    #         exibir_extensao_dupla(arquivos_info)

    # 🌐 Histórico dos navegadores
    if args.chrome:
        print(f"🧭 Recuperando histórico do Google Chrome para {args.usuario}...")
        recuperar_historico_chrome(usuario=args.usuario)

    if args.firefox:
        print(f"🦊 Recuperando histórico do Mozilla Firefox para {args.usuario}...")
        recuperar_historico_firefox(usuario=args.usuario)

    if args.edge:
        print(f"📘 Recuperando histórico do Microsoft Edge para {args.usuario}...")
        recuperar_historico_edge(usuario=args.usuario)

    # 🔍 Análise de padrões incomuns
    if args.analisar_padroes:
        print("📊 Analisando padrões incomuns nos históricos salvos...")
        pasta_historico = "artefatos/historico"
        processar_historico_da_pasta(pasta_historico)

if __name__ == "__main__":
    main()
