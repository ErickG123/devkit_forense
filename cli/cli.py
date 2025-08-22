# -*- coding: utf-8 -*-
import sys
import io
import argparse
import os

from core.browser.browser_history import (
    recuperar_historico_chrome,
    recuperar_historico_edge,
    recuperar_historico_firefox
)
from core.browser.unusual_patterns import processar_historico_da_pasta
from core.network.network_map import build_network_map, save_network_map

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "cli_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="DevKit Forense - Análise de Arquivos e Navegadores")

    parser.add_argument("diretorio", nargs="?", default=None, help="Diretório a ser analisado")
    parser.add_argument("--csv", action="store_true", help="Gerar relatório CSV dos arquivos")
    parser.add_argument("--html", action="store_true", help="Gerar relatório HTML dos arquivos")
    parser.add_argument("--duplicados", action="store_true", help="Exibir arquivos duplicados")
    parser.add_argument("--extensao-dupla", action="store_true", help="Exibir arquivos com extensão dupla")

    parser.add_argument("--chrome", action="store_true", help="Analisar histórico do Google Chrome")
    parser.add_argument("--firefox", action="store_true", help="Analisar histórico do Mozilla Firefox")
    parser.add_argument("--edge", action="store_true", help="Analisar histórico do Microsoft Edge")

    parser.add_argument("--analisar-padroes", action="store_true", help="Detectar padrões incomuns de acesso na pasta 'artefatos/historico'")

    parser.add_argument("--usuario", type=str, default="Usuário Anônimo", help="Nome do usuário para personalização")

    parser.add_argument("--network-map", type=str, help="Gerar mapa de rede (ex: 192.168.0.0/24)")

    args = parser.parse_args()
    print(f"\n🔍 Olá, {args.usuario}! Iniciando a análise...\n")

    if args.chrome:
        print(f"🧭 Recuperando histórico do Google Chrome para {args.usuario}...")
        recuperar_historico_chrome(usuario=args.usuario, output_dir=OUTPUT_DIR)

    if args.firefox:
        print(f"🦊 Recuperando histórico do Mozilla Firefox para {args.usuario}...")
        recuperar_historico_firefox(usuario=args.usuario, output_dir=OUTPUT_DIR)

    if args.edge:
        print(f"📘 Recuperando histórico do Microsoft Edge para {args.usuario}...")
        recuperar_historico_edge(usuario=args.usuario, output_dir=OUTPUT_DIR)

    if args.analisar_padroes:
        print("📊 Analisando padrões incomuns nos históricos salvos...")
        pasta_historico = os.path.join(OUTPUT_DIR, "historico")
        processar_historico_da_pasta(pasta_historico)

    if args.network_map:
        print(f"🌐 Gerando mapa de rede para {args.network_map} ...")
        results = build_network_map(args.network_map)
        save_network_map(results, output_dir=OUTPUT_DIR)

if __name__ == "__main__":
    main()
