import typer
from rich import print

describe_app = typer.Typer()

@describe_app.command("func")
def describe(
    func: str = typer.Argument(..., help="Digite o nome da função que você deseja entender")
):
    docs = {
        "map": {
            "description": "Retorna informações detalhadas de cada host da rede.",
            "example_return": [{
                "host": "192.168.1.1",
                "hostname": "router",
                "mac": "AA:BB:CC:DD:EE:FF",
                "vendor": "Cisco",
                "open_ports": [22, 80],
                "os_info": "Linux"
            }]
        },
        "sweep": {
            "description": "Faz um ping sweep na rede e retorna os hosts ativos.",
            "example_return": ["192.168.1.1", "192.168.1.3"]
        },
        "scan": {
            "description": "Verifica quais portas estão abertas, fechadas e filtradas.",
            "example_return": [{
                "port": 53,
                "protocol": "UDP",
                "status": "open|filtered",
                "banner": "sem resposta",
                "alert": "DNS"
            }]
        },
        "fingerprinting": {
            "description": "Detecta o sistema operacional, tipo de host, serviços e possíveis alertas de vulnerabilidade de um host.",
            "example_return": {
                "os": "Windows",
                "host_type": "Servidor",
                "services": ["SMB", "Web HTTP", "MySQL"],
                "alerts": ["SMB vulnerável (Samba 3.0)"]
            }
        }
    }

    if func in docs:
        info = docs[func]
        print(f"[bold blue]Nome da Função:[/bold blue] {func}")
        print(f"[bold blue]Descrição:[/bold blue] {info['description']}")
        print("[bold blue]Exemplo de Retorno:[/bold blue]")
        print(info['example_return'])
    else:
        typer.echo(f"Função {func} não encontrada.")
