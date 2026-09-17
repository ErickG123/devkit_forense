"""
Módulo de Threat Intelligence Forense (VirusTotal v3 & YARA Scanner).

Permite consultar reputação de hashes SHA-256 e escanear arquivos/diretórios
locais utilizando assinaturas YARA compiladas.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
intel_app = typer.Typer(help="Ferramentas de Threat Intelligence e análise de malware (VirusTotal & YARA)")


def check_virustotal(hash_list: list[str], api_key: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Consulta reputação de lista de hashes SHA-256 na API v3 do VirusTotal.
    Utiliza urllib da biblioteca padrão para evitar dependências adicionais de HTTP.
    """
    key = api_key or os.getenv("VT_API_KEY")
    if not key:
        raise ValueError(
            "Chave de API do VirusTotal não configurada. "
            "Defina a variável de ambiente 'VT_API_KEY' ou utilize a opção '--api-key'."
        )

    results: list[dict[str, Any]] = []

    for file_hash in hash_list:
        clean_hash = file_hash.strip().lower()
        if not clean_hash:
            continue

        url = f"https://www.virustotal.com/api/v3/files/{clean_hash}"
        req = urllib.request.Request(
            url,
            headers={
                "x-apikey": key,
                "Accept": "application/json",
                "User-Agent": "ForenseLab-DFIR/2.0",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                attributes = data.get("data", {}).get("attributes", {})
                stats = attributes.get("last_analysis_stats", {})
                results.append({
                    "hash": clean_hash,
                    "status": "FOUND",
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "undetected": stats.get("undetected", 0),
                    "meaningful_name": attributes.get("meaningful_name", "Desconhecido"),
                    "type_description": attributes.get("type_description", "Desconhecido"),
                })
        except urllib.error.HTTPError as e:
            if e.code == 404:
                results.append({
                    "hash": clean_hash,
                    "status": "NOT_FOUND",
                    "malicious": 0,
                    "suspicious": 0,
                    "harmless": 0,
                    "undetected": 0,
                    "meaningful_name": "-",
                    "type_description": "Não encontrado na base do VirusTotal",
                })
            elif e.code == 401 or e.code == 403:
                raise PermissionError("Chave de API do VirusTotal inválida ou sem permissões.") from e
            else:
                results.append({
                    "hash": clean_hash,
                    "status": f"HTTP_ERROR_{e.code}",
                    "malicious": 0,
                    "suspicious": 0,
                    "harmless": 0,
                    "undetected": 0,
                    "meaningful_name": "-",
                    "type_description": f"Erro na requisição: {e}",
                })
        except Exception as e:
            results.append({
                "hash": clean_hash,
                "status": "CONNECTION_ERROR",
                "malicious": 0,
                "suspicious": 0,
                "harmless": 0,
                "undetected": 0,
                "meaningful_name": "-",
                "type_description": str(e),
            })

    return results


def scan_with_yara(target_path: Path, rules_file: Path) -> list[dict[str, Any]]:
    """
    Executa varredura de assinaturas YARA no alvo.
    Prioriza o pacote 'yara' se instalado; caso contrário, busca o executável 'yara' no PATH do sistema.
    """
    if not rules_file.is_file():
        raise FileNotFoundError(f"Arquivo de regras YARA não encontrado em: {rules_file}")
    if not target_path.exists():
        raise FileNotFoundError(f"Alvo de varredura YARA não encontrado em: {target_path}")

    # 1. Tenta biblioteca nativa yara-python se disponível
    try:
        import yara  # type: ignore

        rules = yara.compile(filepath=str(rules_file))
        matches_found: list[dict[str, Any]] = []

        if target_path.is_file():
            files_to_scan = [target_path]
        else:
            files_to_scan = [p for p in target_path.rglob("*") if p.is_file()]

        for f in files_to_scan:
            try:
                m_list = rules.match(str(f))
                for m in m_list:
                    matches_found.append({
                        "file": str(f),
                        "rule": m.rule,
                        "tags": m.tags,
                        "strings": [str(s) for s in m.strings],
                    })
            except Exception:
                continue

        return matches_found

    except ImportError:
        pass

    # 2. Fallback: Executável de linha de comando yara no PATH
    yara_bin = shutil.which("yara") or shutil.which("yara.exe")
    if not yara_bin:
        raise RuntimeError(
            "Motor YARA não disponível. Instale o pacote 'yara-python' (pip install yara-python) "
            "ou adicione o binário 'yara' ao PATH do sistema operacional."
        )

    cmd = [yara_bin, "-s", str(rules_file), str(target_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    matches_found = []
    current_rule = "unknown"
    current_file = str(target_path)

    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Linha de match padrão yara: <rule_name> <path>
        parts = line.split(" ", 1)
        if len(parts) == 2 and not line.startswith("0x"):
            current_rule, current_file = parts[0], parts[1]
            matches_found.append({
                "file": current_file,
                "rule": current_rule,
                "tags": [],
                "strings": [],
            })
        elif line.startswith("0x") and matches_found:
            matches_found[-1]["strings"].append(line)

    return matches_found


@intel_app.command("virustotal", help="Consulta reputação de hashes SHA-256 no VirusTotal v3")
def virustotal_cmd(
    hashes: list[str] = typer.Argument(..., help="Um ou mais hashes SHA-256 para consultar"),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Chave de API do VirusTotal (ou defina a variável VT_API_KEY)",
    ),
):
    try:
        with console.status("[bold cyan]Consultando VirusTotal API v3...[/bold cyan]"):
            results = check_virustotal(hashes, api_key=api_key)

        table = Table(title="Resultados Threat Intelligence (VirusTotal v3)")
        table.add_column("SHA-256", style="cyan", overflow="fold")
        table.add_column("Status", style="magenta")
        table.add_column("Malicioso", justify="right", style="red")
        table.add_column("Suspeito", justify="right", style="yellow")
        table.add_column("Inofensivo", justify="right", style="green")
        table.add_column("Nome / Tipo", style="white", overflow="fold")

        for r in results:
            malicious_style = "[bold red]" if r["malicious"] > 0 else "[green]"
            table.add_row(
                r["hash"],
                r["status"],
                f"{malicious_style}{r['malicious']}[/]",
                str(r["suspicious"]),
                str(r["harmless"]),
                f"{r['meaningful_name']} ({r['type_description']})",
            )

        console.print(table)

    except ValueError as e:
        console.print(Panel(f"[bold yellow]{e}[/bold yellow]", title="Chave de API Ausente"))
        raise typer.Exit(code=1)
    except PermissionError as e:
        console.print(Panel(f"[bold red]{e}[/bold red]", title="Autenticação Rejeitada"))
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao consultar VirusTotal: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)


@intel_app.command("yara", help="Escaneia diretório ou arquivo local utilizando regras YARA")
def yara_cmd(
    target: Path = typer.Option(..., "--target", "-t", help="Arquivo ou pasta para escanear", resolve_path=True),
    rules: Path = typer.Option(..., "--rules", "-r", help="Arquivo contendo as regras YARA (.yar)", resolve_path=True),
):
    try:
        with console.status(f"[bold green]Escaneando '{target.name}' com regras YARA...[/bold green]"):
            matches = scan_with_yara(target, rules)

        table = Table(title=f"Varredura YARA ({len(matches)} correspondências detectadas)")
        table.add_column("Arquivo Evidência", style="cyan", overflow="fold")
        table.add_column("Regra Disparada", style="bold red")
        table.add_column("Strings Detectadas", style="yellow", overflow="fold")

        if matches:
            for m in matches:
                strings_preview = "\n".join(m["strings"][:3]) or "Match por padrão heurístico"
                table.add_row(m["file"], m["rule"], strings_preview)
            console.print(table)
        else:
            console.print(f"[bold green][OK] Nenhuma ameaça correspondente encontrada para '{target.name}'.[/bold green]")

    except Exception as e:
        console.print(Panel(f"[bold red]Erro durante varredura YARA: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)
