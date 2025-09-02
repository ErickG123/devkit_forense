import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def carregar_json(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)

def tratar_data_acesso(data_str):
    try:
        if data_str == "N/A" or not data_str:
            return None
        return pd.to_datetime(data_str, format="%Y-%m-%d %H:%M:%S", errors='raise')
    except Exception as e:
        print(f"[ALERTA] Erro ao processar data: {data_str}. Erro: {e}")
        return None

def detectar_acessos_horarios_diferentes(df, output_dir=None, arquivo_prefixo=""):
    df['ultimo_acesso'] = df['ultimo_acesso'].apply(tratar_data_acesso)
    df = df.dropna(subset=['ultimo_acesso']).copy()
    df.loc[:, 'hora'] = df['ultimo_acesso'].dt.hour

    acessos_madrugada = df[df['hora'].between(0, 6)]
    acessos_manha = df[df['hora'].between(7, 11)]
    acessos_tarde = df[df['hora'].between(12, 17)]
    acessos_noite = df[df['hora'].between(18, 23)]

    plt.figure(figsize=(10, 6))
    acessos_por_hora = df['hora'].value_counts().sort_index()
    acessos_por_hora.plot(kind='bar', color='skyblue')
    plt.title('Acessos por Hora do Dia')
    plt.xlabel('Hora')
    plt.ylabel('Número de Acessos')
    plt.xticks(rotation=0)
    plt.tight_layout()

    if output_dir:
        caminho_grafico = os.path.join(output_dir, f"{arquivo_prefixo}acessos_por_hora.png")
        plt.savefig(caminho_grafico)
        plt.close()
        print(f"[INFO] Gráfico salvo em: {caminho_grafico}")
    else:
        plt.show()

    acessos_por_periodo = {
        "Madrugada (00h-06h)": len(acessos_madrugada),
        "Manhã (07h-11h)": len(acessos_manha),
        "Tarde (12h-17h)": len(acessos_tarde),
        "Noite (18h-23h)": len(acessos_noite),
    }
    print("\nAcessos por período:")
    print(pd.DataFrame(list(acessos_por_periodo.items()), columns=["Período", "Quantidade de Acessos"]))

    acessos_incomuns = pd.concat([acessos_madrugada, acessos_noite])
    if not acessos_incomuns.empty:
        print(f"\nAcessos em horários incomuns (madrugada/noite):")
        print(acessos_incomuns[['url', 'ultimo_acesso']].head())

def detectar_acessos_repetidos(df, intervalo_maximo=5):
    df['ultimo_acesso'] = pd.to_datetime(df['ultimo_acesso'])
    df['diferenca'] = df['ultimo_acesso'].diff().fillna(pd.Timedelta(seconds=0))

    acessos_repetidos = df[df['diferenca'] < pd.Timedelta(minutes=intervalo_maximo)]

    if not acessos_repetidos.empty:
        print(f"\nAcessos repetidos detectados em intervalos menores que {intervalo_maximo} minutos:")
        print(acessos_repetidos[['url', 'ultimo_acesso', 'diferenca']].head())

def processar_historico_da_pasta(pasta, output_dir=None):
    arquivos_json = [f for f in os.listdir(pasta) if f.endswith('.json')]

    if not arquivos_json:
        print("[ALERTA] Nenhum arquivo JSON encontrado na pasta especificada.")
        return

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    for arquivo in arquivos_json:
        caminho_arquivo = os.path.join(pasta, arquivo)
        try:
            print(f"\n[INFO] Processando arquivo: {caminho_arquivo}")

            dados = carregar_json(caminho_arquivo)

            if "historico_completo" in dados:
                lista_acessos = dados["historico_completo"]
            elif "ultimas_10_urls" in dados:
                lista_acessos = dados["ultimas_10_urls"]
            else:
                print(f"[AVISO] Nenhum histórico válido encontrado em {arquivo}")
                continue

            df = pd.DataFrame(lista_acessos).copy()

            prefixo = os.path.splitext(arquivo)[0] + "_"
            detectar_acessos_horarios_diferentes(df, output_dir=output_dir, arquivo_prefixo=prefixo)
            detectar_acessos_repetidos(df, intervalo_maximo=5)

        except Exception as erro:
            print(f"\n❌ Erro ao processar o arquivo {arquivo}: {erro}")

if __name__ == "__main__":
    try:
        pasta_json = "artefatos/historico"
        output_dir = "artefatos/patterns_output"
        processar_historico_da_pasta(pasta_json, output_dir=output_dir)
    except Exception as erro:
        print(f"\n❌ Erro geral: {erro}")
