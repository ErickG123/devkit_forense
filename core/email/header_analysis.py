import os
import json
import csv
import re
from datetime import datetime

SPF_REGEX = re.compile(r"spf=(pass|fail|softfail|neutral)", re.IGNORECASE)
DKIM_REGEX = re.compile(r"dkim=(pass|fail|none)", re.IGNORECASE)
DMARC_REGEX = re.compile(r"dmarc=(pass|fail|none)", re.IGNORECASE)
IP_REGEX = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")

def extract_ips_from_received(received_headers):
    ips = []
    if not received_headers:
        return ips
    if isinstance(received_headers, str):
        received_headers = [received_headers]
    for header in received_headers:
        found_ips = IP_REGEX.findall(header)
        ips.extend(found_ips)
    return list(set(ips))

def analyze_email_headers(email_data):
    headers_to_check = ["received", "authentication-results", "spf", "dkim", "dmarc"]

    result = {
        "subject": email_data.get("subject"),
        "from": email_data.get("from"),
        "to": email_data.get("to"),
        "date": email_data.get("date"),
        "message_id": email_data.get("message_id"),
        "spf": "Desconhecido",
        "dkim": "Desconhecido",
        "dmarc": "Desconhecido",
        "origin_ips": [],
    }

    received_headers = email_data.get("received", [])
    if received_headers:
        result["origin_ips"] = extract_ips_from_received(received_headers)

    auth_results = email_data.get("authentication_results", "")
    if auth_results:
        spf_match = SPF_REGEX.search(auth_results)
        dkim_match = DKIM_REGEX.search(auth_results)
        dmarc_match = DMARC_REGEX.search(auth_results)
        if spf_match:
            result["spf"] = spf_match.group(1).lower()
        if dkim_match:
            result["dkim"] = dkim_match.group(1).lower()
        if dmarc_match:
            result["dmarc"] = dmarc_match.group(1).lower()

    return result

def analyze_emails_from_json(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        emails = json.load(f)

    analyzed_results = []
    for email_data in emails:
        analyzed_results.append(analyze_email_headers(email_data))
    return analyzed_results

def export_analysis(results, prefix="email_header_analysis"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"{prefix}_{timestamp}.json"
    csv_file = f"{prefix}_{timestamp}.csv"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    headers = ["subject", "from", "to", "date", "message_id", "spf", "dkim", "dmarc", "origin_ips"]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in results:
            r_copy = r.copy()
            r_copy["origin_ips"] = ", ".join(r_copy["origin_ips"])
            writer.writerow(r_copy)

    print(f"\n✅ Análise de cabeçalhos salva em JSON: {json_file} e CSV: {csv_file}")

if __name__ == "__main__":
    json_input = input("Digite o caminho do JSON gerado pelo email_parser: ").strip()
    results = analyze_emails_from_json(json_input)
    export_analysis(results)
