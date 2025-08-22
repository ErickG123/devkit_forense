import json
from collections import Counter
from datetime import datetime

json_file = "network_map_20250822_100710.json"
output_file = f"network_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

with open(json_file, "r", encoding="utf-8") as f:
    network_data = json.load(f)

ports_counter = Counter()
alerts = []

html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório de Rede</title>
<style>
    body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
    h1 {{ color: #333; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background-color: #555; color: white; }}
    tr:nth-child(even) {{ background-color: #eee; }}
    .alert {{ color: red; font-weight: bold; }}
</style>
</head>
<body>
<h1>Relatório de Rede - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</h1>
<h2>Total de hosts ativos: {len(network_data)}</h2>
<table>
<tr>
    <th>IP</th>
    <th>Hostname</th>
    <th>MAC</th>
    <th>Fabricante</th>
    <th>Portas Abertas</th>
</tr>
"""

for host in network_data:
    portas_html = ""
    if host['ports']:
        for port_info in host['ports']:
            port = port_info['port']
            proto = port_info['protocol']
            banner = port_info['banner']
            alert = port_info.get('alert')
            ports_counter[f"{port}/{proto}"] += 1
            if alert:
                alerts.append(f"{host['ip']}:{port}/{proto} -> {alert}")
                portas_html += f"<span class='alert'>{port}/{proto} - {banner} ⚠ {alert}</span><br>"
            else:
                portas_html += f"{port}/{proto} - {banner}<br>"
    else:
        portas_html = "Nenhuma porta aberta encontrada."

    html += f"""
    <tr>
        <td>{host['ip']}</td>
        <td>{host['hostname']}</td>
        <td>{host['mac']}</td>
        <td>{host['vendor']}</td>
        <td>{portas_html}</td>
    </tr>
    """

html += "</table>"

html += "<h2>Estatísticas de portas abertas</h2><ul>"
for port, count in ports_counter.most_common():
    html += f"<li>{port}: {count} host(s)</li>"
html += "</ul>"

html += "<h2>Alertas encontrados</h2>"
if alerts:
    html += "<ul>"
    for a in alerts:
        html += f"<li class='alert'>{a}</li>"
    html += "</ul>"
else:
    html += "<p>Nenhum alerta encontrado.</p>"

html += """
</body>
</html>
"""

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Relatório HTML gerado: {output_file}")
