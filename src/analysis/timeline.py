"""
Motor de Super Timeline Forense (Padrão Ouro DFIR).

Ingere artefatos heterogêneos gerados pelos módulos Go (Histórico, Downloads, Logins,
Varreduras de Rede e E-mails), normaliza carimbos de data/hora para UTC ISO-8601
e consolida uma linha do tempo unificada de eventos periciais (Plaso / Log2Timeline style).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
timeline_app = typer.Typer(help="Geração e análise de Super Timeline cronológica integrada (DFIR)")


def normalize_timestamp(raw_val: Any) -> Optional[datetime]:
    """
    Normaliza formatos de data e hora (ISO-8601, RFC3339, Unix Epoch, etc.)
    para datetime em UTC com fuso horário explícito.
    Zero dependências externas (stdlib pura).
    """
    if not raw_val:
        return None

    # Se já for inteiro/float (Unix Epoch seconds)
    if isinstance(raw_val, (int, float)):
        try:
            return datetime.fromtimestamp(raw_val, tz=timezone.utc)
        except Exception:
            return None

    if isinstance(raw_val, str):
        raw_str = raw_val.strip()
        if not raw_str or raw_str in ("-", "N/A", "null"):
            return None
        
        # 1. Tenta datetime.fromisoformat nativo (suporta ISO-8601 e RFC3339 moderno com 'Z')
        iso_candidate = raw_str.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(iso_candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception:
            pass

        # 2. Formatos comuns em forensics (Apache/HTTP date, SQLite string 'YYYY-MM-DD HH:MM:SS')
        common_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
        ]
        for fmt in common_formats:
            try:
                dt = datetime.strptime(raw_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt
            except Exception:
                continue

    return None


def ingest_artifacts_folder(artifacts_dir: Path) -> list[dict[str, Any]]:
    """
    Varre um diretório procurando arquivos de evidências (.json e .ndjson)
    e extrai eventos padronizados para a Super Timeline.
    """
    if not artifacts_dir.is_dir():
        raise FileNotFoundError(f"Diretório de artefatos não encontrado: {artifacts_dir}")

    timeline_events: list[dict[str, Any]] = []

    # Procura todos os arquivos JSON e NDJSON
    candidate_files = list(artifacts_dir.glob("**/*.json")) + list(artifacts_dir.glob("**/*.ndjson"))

    for file_path in candidate_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace").strip()
            if not content:
                continue

            records: list[dict[str, Any]] = []

            # Tenta decodificar como JSON array ou envelope
            if content.startswith("["):
                try:
                    records = json.loads(content)
                except json.JSONDecodeError:
                    pass
            elif content.startswith("{"):
                # Pode ser um envelope de resposta ou NDJSON
                try:
                    single_json = json.loads(content)
                    if "data" in single_json and isinstance(single_json["data"], dict):
                        # Extrai registros de data
                        for k in ("records", "credentials", "active_hosts", "open_ports"):
                            if k in single_json["data"]:
                                records = single_json["data"][k]
                                break
                    else:
                        records = [single_json]
                except json.JSONDecodeError:
                    pass

            # Se não conseguiu decodificar como bloco único, processa linha a linha (NDJSON)
            if not records:
                for line in content.splitlines():
                    clean = line.strip()
                    if clean:
                        try:
                            records.append(json.loads(clean))
                        except json.JSONDecodeError:
                            continue

            # Mapeia eventos para a Super Timeline
            for item in records:
                if not isinstance(item, dict):
                    continue

                source_type = "DESCONHECIDO"
                description = ""
                raw_time = None

                # 1. Histórico de Navegador
                if "last_visit_utc" in item or ("url" in item and "visit_count" in item):
                    source_type = "BROWSER_HISTORY"
                    raw_time = item.get("last_visit_utc")
                    description = f"Visita a '{item.get('title') or item.get('url')}' ({item.get('browser', 'Chromium')})"

                # 2. Downloads de Navegador
                elif "received_bytes" in item or "target_file" in item:
                    source_type = "FILE_DOWNLOAD"
                    raw_time = item.get("start_time_utc") or item.get("end_time_utc")
                    description = f"Download de '{item.get('target_file')}' ({item.get('state')}) via {item.get('browser', 'Browser')}"

                # 3. Credenciais / Logins
                elif "password" in item or "origin_url" in item:
                    source_type = "CREDENTIAL_STORED"
                    raw_time = item.get("created_utc")
                    description = f"Credencial armazenada para '{item.get('username')}' em {item.get('origin_url')}"

                # 4. Varredura de Rede (Host Ativo)
                elif "ip" in item and "status" in item:
                    source_type = "NETWORK_HOST"
                    raw_time = item.get("timestamp")
                    description = f"Host {item.get('ip')} detectado ONLINE via {item.get('method', 'tcp')}"

                # 5. E-mails
                elif "Subject" in item or "From" in item:
                    source_type = "EMAIL_MESSAGE"
                    raw_time = item.get("Date") or item.get("date")
                    description = f"E-mail de '{item.get('From', '-')}' com assunto: '{item.get('Subject', '-')}'"

                dt = normalize_timestamp(raw_time)
                if dt:
                    timeline_events.append({
                        "datetime_utc": dt,
                        "timestamp_str": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "source": source_type,
                        "description": description,
                        "raw_data": item,
                    })

        except Exception:
            continue

    # Ordena cronologicamente: do evento mais antigo para o mais recente
    timeline_events.sort(key=lambda x: x["datetime_utc"])
    return timeline_events


@timeline_app.command("generate", help="Gera uma Super Timeline cronológica integrando evidências heterogêneas")
def generate_timeline(
    directory: Path = typer.Option(
        Path("artefatos"),
        "--dir",
        "-d",
        help="Pasta contendo as evidências extraídas (JSON/NDJSON)",
        resolve_path=True,
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Quantidade máxima de eventos para exibir no terminal"),
    output_json: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Arquivo JSON para exportar a timeline consolidada",
        resolve_path=True,
    ),
):
    try:
        with console.status(f"[bold cyan]Consolidando Super Timeline a partir de '{directory}'...[/bold cyan]"):
            events = ingest_artifacts_folder(directory)

        table = Table(title=f"Super Timeline DFIR - ForenseLab ({len(events)} eventos cronológicos)")
        table.add_column("Timestamp (UTC)", style="cyan", width=22)
        table.add_column("Fonte / Tipo", style="magenta", width=20)
        table.add_column("Descrição do Evento", style="white", overflow="fold")

        if not events:
            console.print(f"[bold yellow]Nenhum evento com timestamp válido localizado em: {directory}[/bold yellow]")
            return

        for ev in events[:limit]:
            source_color = "green" if "BROWSER" in ev["source"] else "yellow" if "DOWNLOAD" in ev["source"] else "red"
            table.add_row(
                ev["timestamp_str"],
                f"[{source_color}]{ev['source']}[/]",
                ev["description"],
            )

        console.print(table)
        console.print(f"[bold green][OK] Total de eventos integrados: {len(events)}[/bold green]")

        if output_json:
            export_payload = [
                {
                    "timestamp": ev["timestamp_str"],
                    "source": ev["source"],
                    "description": ev["description"],
                    "data": ev["raw_data"],
                }
                for ev in events
            ]
            output_json.parent.mkdir(parents=True, exist_ok=True)
            output_json.write_text(json.dumps(export_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            console.print(f"[bold green]✅ Timeline exportada com sucesso em: {output_json}[/bold green]")

    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao gerar Super Timeline: {e}[/bold red]", title="Erro"))
        raise typer.Exit(code=1)
