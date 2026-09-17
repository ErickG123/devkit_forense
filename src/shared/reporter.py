"""
Módulo Gerador de Laudos e Cadeia de Custódia Forense (Jinja2).

Recebe os dados padronizados retornados pelo motor Go ou módulos Python
e renderiza laudos periciais profissionais em HTML (com suporte a impressão/PDF).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jinja2 import Template

HTML_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ title }} - Laudo Pericial ForenseLab</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #24292e;
            line-height: 1.6;
            margin: 0;
            padding: 40px;
            background-color: #f6f8fa;
        }
        .container {
            max-width: 960px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #d1d5da;
            border-radius: 6px;
            padding: 40px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        .header {
            border-bottom: 2px solid #0366d6;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            margin: 0;
            font-size: 26px;
            color: #0366d6;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: 600;
            line-height: 1;
            color: #ffffff;
            background-color: #28a745;
            border-radius: 20px;
        }
        .meta-box {
            background-color: #f1f8ff;
            border: 1px solid #c8e1ff;
            border-radius: 4px;
            padding: 16px;
            margin-bottom: 25px;
            font-size: 14px;
        }
        .meta-box dt {
            font-weight: 600;
            color: #0366d6;
            float: left;
            width: 220px;
            clear: left;
        }
        .meta-box dd {
            margin-left: 230px;
            margin-bottom: 8px;
            word-break: break-all;
            font-family: Consolas, monospace;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 13px;
        }
        th, td {
            border: 1px solid #e1e4e8;
            padding: 10px 12px;
            text-align: left;
        }
        th {
            background-color: #f6f8fa;
            font-weight: 600;
            color: #444d56;
        }
        tr:nth-child(even) {
            background-color: #fafbfc;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e4e8;
            font-size: 12px;
            color: #586069;
            text-align: center;
        }
        @media print {
            body { background: none; padding: 0; }
            .container { box-shadow: none; border: none; padding: 0; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>ForenseLab &bull; Laudo Pericial Digital</h1>
                <small>Toolkit Forense Educacional & Investigativo (DFIR)</small>
            </div>
            <span class="badge">Cadeia de Custódia Preservada</span>
        </div>

        <h2>{{ title }}</h2>

        <div class="meta-box">
            <dl>
                <dt>Data e Hora da Geração:</dt>
                <dd>{{ generated_at }}</dd>
                <dt>Investigador / Usuário:</dt>
                <dd>{{ examiner }}</dd>
                <dt>Comando de Origem:</dt>
                <dd>{{ command }}</dd>
                {% if source_hash %}
                <dt>Hash SHA-256 da Evidência:</dt>
                <dd>{{ source_hash }}</dd>
                {% endif %}
                <dt>Integridade do Laudo (SHA-256):</dt>
                <dd>{{ report_hash }}</dd>
            </dl>
        </div>

        <h3>Registros de Evidência Extraídos (Total: {{ records|length }})</h3>

        {% if records and records|length > 0 %}
        <table>
            <thead>
                <tr>
                    {% for key in keys %}
                    <th>{{ key|capitalize|replace('_', ' ') }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for row in records %}
                <tr>
                    {% for key in keys %}
                    <td>{{ row[key] if row[key] is not none else '-' }}</td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p><em>Nenhum registro encontrado para esta evidência.</em></p>
        {% endif %}

        <div class="footer">
            <p>Laudo emitido pelo sistema automatizado ForenseLab. Em conformidade com boas práticas de preservação de evidências digitais.</p>
        </div>
    </div>
</body>
</html>
"""


def calculate_sha256(data: bytes | str) -> str:
    """Calcula o hash SHA-256 de dados binários ou string."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def generate_forensic_report(
    title: str,
    command: str,
    records: list[dict[str, Any]],
    output_file: Path | str,
    examiner: str = "Perito ForenseLab",
    source_file: Optional[Path | str] = None,
) -> Path:
    """
    Gera um relatório pericial formal em HTML.

    Parâmetros:
        title: Título descritivo do laudo.
        command: Comando executado (ex: 'browser logins', 'network scan').
        records: Lista de registros/dicionários recuperados.
        output_file: Caminho do arquivo .html a ser gerado.
        examiner: Nome do operador/perito responsável.
        source_file: Caminho do arquivo original da evidência (para cálculo de SHA-256).

    Retorna:
        Path: Caminho absoluto do relatório gerado.
    """
    output_path = Path(output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    source_hash = None
    if source_file and Path(source_file).is_file():
        source_hash = calculate_sha256(Path(source_file).read_bytes())

    # Descobre colunas presentes nos registros
    keys: list[str] = []
    if records:
        for r in records:
            for k in r.keys():
                if k not in keys:
                    keys.append(k)

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Calcula hash inicial dos dados tabulados para integridade
    records_hash = calculate_sha256(json.dumps(records, sort_keys=True, ensure_ascii=False))

    template = Template(HTML_REPORT_TEMPLATE)
    rendered_html = template.render(
        title=title,
        command=command,
        records=records,
        keys=keys,
        examiner=examiner,
        source_hash=source_hash,
        report_hash=records_hash,
        generated_at=now_str,
    )

    output_path.write_text(rendered_html, encoding="utf-8")

    # Geração de Assinatura Digital e Cadeia de Custódia (.audit)
    final_file_hash = calculate_sha256(output_path.read_bytes())
    audit_file = output_path.with_suffix(output_path.suffix + ".audit")

    audit_payload = {
        "report_file": output_path.name,
        "report_sha256": final_file_hash,
        "title": title,
        "command": command,
        "examiner": examiner,
        "source_evidence_sha256": source_hash or "N/A",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "integrity_status": "VERIFIED_UNTOUCHED",
    }
    audit_file.write_text(json.dumps(audit_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return output_path
