# -*- coding: utf-8 -*-
import sys
import io
import os
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.browser.unusual_patterns import processar_historico_da_pasta
from core.registry import FUNCTIONALITIES

OUTPUT_DIR = os.path.join(BASE_DIR, "cli_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="DevKit Forense - Análise de Arquivos e Navegadores")

    parser.add_argument("diretorio", nargs="?", default=None, help="Diretório a ser analisado")
    parser.add_argument("--chrome", action="store_true", help="Analisar histórico do Google Chrome")
    parser.add_argument("--firefox", action="store_true", help="Analisar histórico do Mozilla Firefox")
    parser.add_argument("--edge", action="store_true", help="Analisar histórico do Microsoft Edge")
    parser.add_argument("--analisar-padroes", action="store_true", help="Detectar padrões incomuns de acesso na pasta 'artefatos/historico'")
    parser.add_argument("--usuario", type=str, default="Usuário Anônimo", help="Nome do usuário")
    parser.add_argument("--network", help="Executa o mapeamento de rede (ex: 192.168.0.0/24)")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Diretório para salvar os resultados")

    args = parser.parse_args()
    print(f"\n🔍 Olá, {args.usuario}! Iniciando a análise...\n")

    ARG_TO_FUNC = {
        "network": "network_map",
        "chrome": "chrome_history",
        "firefox": "firefox_history",
        "edge": "edge_history",
    }

    for arg_name, func_key in ARG_TO_FUNC.items():
        if getattr(args, arg_name):
            func = FUNCTIONALITIES[func_key]
            print(f"🟢 Executando {func_key}...")

            try:
                if func_key == "network_map":
                    result = func(args.network, args.output_dir)
                    print("✅ Mapeamento concluído com sucesso!")
                    print(f"📁 Arquivos gerados:\n - {result.get('json_file')}\n - {result.get('csv_file')}")
                else:
                    func(usuario=args.usuario, output_dir=args.output_dir)
                    print(f"✅ {func_key} concluído!")
            except Exception as e:
                print(f"❌ Erro ao executar {func_key}: {e}")

    if args.analisar_padroes:
        print("📊 Analisando padrões incomuns nos históricos salvos...")
        pasta_historico = os.path.join(args.output_dir, "historico")
        processar_historico_da_pasta(pasta_historico)

    if not any([args.network, args.chrome, args.firefox, args.edge, args.analisar_padroes]):
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Erro ao executar CLI: {e}")
        sys.exit(1)
