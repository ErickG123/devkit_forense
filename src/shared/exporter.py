"""
Módulo de exportação genérico do ForenseLab.

Centraliza a responsabilidade de serializar e salvar resultados em disco,
eliminando código de I/O duplicado nas camadas de CLI e API.

Uso:
    from shared.exporter import export_data, ExportFormat
    from pathlib import Path

    export_data(results, fmt=ExportFormat.JSON, output_dir=Path("artefatos"), stem="scan_results")
"""

import csv
import json
import logging
from enum import Enum
from pathlib import Path

logger = logging.getLogger("forenselab.shared.exporter")


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------


class ExportFormat(str, Enum):
    """Formatos de exportação suportados — compatível com typer.Option(enum)."""

    JSON = "json"
    CSV = "csv"


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _flatten_for_csv(data: dict | list) -> list[dict]:
    """
    Normaliza `data` para uma lista plana de dicionários.

    - list[dict]  → retorna como está.
    - dict        → envolve em lista com um único item.
    - list[scalar] → converte cada item em {"value": item}.
    """
    if isinstance(data, list):
        if not data:
            return []
        if isinstance(data[0], dict):
            return data
        # lista de escalares (ex: IPs do sweep)
        return [{"value": item} for item in data]
    if isinstance(data, dict):
        return [data]
    return [{"value": str(data)}]


def _write_json(data: dict | list, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False, default=str)


def _write_csv(data: dict | list, path: Path) -> None:
    rows = _flatten_for_csv(data)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    # Coleta todas as chaves possíveis preservando a ordem de inserção
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            # Serializa listas/dicts aninhados como string JSON para não perder dados
            safe_row = {
                k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                for k, v in row.items()
            }
            writer.writerow(safe_row)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def export_data(
    data: dict | list,
    fmt: ExportFormat | str,
    output_dir: Path,
    stem: str = "export",
) -> Path:
    """
    Exporta `data` para um arquivo no formato `fmt` dentro de `output_dir`.

    Parameters
    ----------
    data:
        Dicionário ou lista pura retornada pelo Core.
    fmt:
        Formato desejado: ``ExportFormat.JSON`` / ``"json"``
        ou ``ExportFormat.CSV`` / ``"csv"``.
    output_dir:
        Diretório de destino — será criado se não existir.
    stem:
        Nome-base do arquivo (sem extensão). Padrão: ``"export"``.

    Returns
    -------
    Path
        Caminho absoluto do arquivo gerado.

    Raises
    ------
    ValueError
        Se `fmt` não for um formato suportado.
    OSError
        Se o arquivo não puder ser escrito (permissão, disco cheio, etc.).

    Examples
    --------
    >>> path = export_data(results, "json", Path("artefatos/network"), stem="port_scan")
    >>> # → artefatos/network/port_scan.json

    >>> path = export_data(hosts, ExportFormat.CSV, Path("artefatos"), stem="sweep")
    >>> # → artefatos/sweep.csv
    """
    fmt_normalized = ExportFormat(str(fmt).lower()) if not isinstance(fmt, ExportFormat) else fmt

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dest = output_dir / f"{stem}.{fmt_normalized.value}"

    logger.debug("Exportando dados para '%s' (formato: %s).", dest, fmt_normalized.value)

    match fmt_normalized:
        case ExportFormat.JSON:
            _write_json(data, dest)
        case ExportFormat.CSV:
            _write_csv(data, dest)
        case _:  # pragma: no cover — Enum já valida antes de chegar aqui
            raise ValueError(f"Formato não suportado: {fmt!r}. Use 'json' ou 'csv'.")

    logger.info("Exportação concluída → %s", dest)
    return dest
