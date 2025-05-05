import argparse
from modules.file_inspector import inspecionar_diretorio, gerar_relatorio_csv, gerar_relatorio_html, exibir_arquivos_duplicados, exibir_extensao_dupla
from modules.browser_history import recuperar_historico  # Importando o módulo de recuperação de histórico

def main():
    # Inicializando o parser para CLI
    parser = argparse.ArgumentParser(description="Ferramentas Forenses de Análise de Arquivos e Histórico de Navegação")

    # Definindo os argumentos para a CLI de análise de arquivos
    parser.add_argument("diretorio", help="Caminho para o diretório a ser analisado", type=str, nargs="?", default=None)
    parser.add_argument("--csv", help="Gerar relatório em formato CSV", action="store_true")
    parser.add_argument("--html", help="Gerar relatório em formato HTML", action="store_true")
    parser.add_argument("--duplicados", help="Exibir arquivos duplicados por hash", action="store_true")
    parser.add_argument("--extensao-dupla", help="Exibir arquivos com extensão dupla suspeita", action="store_true")

    # Definindo os argumentos para recuperação de histórico
    parser.add_argument("--chrome", help="Recuperar histórico do Google Chrome", action="store_true")
    parser.add_argument("--firefox", help="Recuperar histórico do Mozilla Firefox", action="store_true")
    parser.add_argument("--edge", help="Recuperar histórico do Microsoft Edge", action="store_true")

    # Adicionando o argumento para nome de usuário personalizado
    parser.add_argument("--usuario", help="Nome do usuário para personalizar a execução", type=str, default="Usuário Anônimo")

    # Parseando os argumentos da CLI
    args = parser.parse_args()

    # Exibindo o nome do usuário
    print(f"Olá, {args.usuario}! Iniciando a análise...")

    # Chama a função de inspeção do diretório, passando o diretório (apenas para file_inspector)
    if args.diretorio:
        arquivos_info, hashes = inspecionar_diretorio(args.diretorio)

        # Gerar relatório conforme a opção do usuário
        if args.csv:
            gerar_relatorio_csv(arquivos_info)
        if args.html:
            gerar_relatorio_html(arquivos_info)

        # Exibir duplicados e arquivos com extensão dupla, se solicitado
        if args.duplicados:
            exibir_arquivos_duplicados(hashes)
        if args.extensao_dupla:
            exibir_extensao_dupla(arquivos_info)

    # Chama a função de recuperação de histórico, caso o usuário tenha solicitado
    if args.chrome:
        print(f"Recuperando histórico do Google Chrome para o usuário {args.usuario}...")
        recuperar_historico(chrome=True, usuario=args.usuario)
    elif args.firefox:
        print(f"Recuperando histórico do Mozilla Firefox para o usuário {args.usuario}...")
        recuperar_historico(firefox=True, usuario=args.usuario)
    elif args.edge:
        print(f"Recuperando histórico do Microsoft Edge para o usuário {args.usuario}...")
        recuperar_historico(edge=True, usuario=args.usuario)

if __name__ == "__main__":
    main()
