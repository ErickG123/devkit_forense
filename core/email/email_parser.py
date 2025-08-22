import os
import json
import csv
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime
import hashlib

BASE_DIR = os.getcwd()
ATTACHMENT_DIR = os.path.join(BASE_DIR, "attachments")
os.makedirs(ATTACHMENT_DIR, exist_ok=True)

def hash_file(filepath, method="md5"):
    h = hashlib.md5() if method == "md5" else hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_eml_file(filepath):
    with open(filepath, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    email_data = {
        "subject": msg.get("subject"),
        "from": msg.get("from"),
        "to": msg.get("to"),
        "cc": msg.get("cc"),
        "bcc": msg.get("bcc"),
        "date": msg.get("date"),
        "message_id": msg.get("message-id"),
        "attachments": []
    }

    for part in msg.iter_attachments():
        filename = part.get_filename()
        if filename:
            safe_filename = filename.replace("/", "_").replace("\\", "_")
            filepath = os.path.join(ATTACHMENT_DIR, safe_filename)
            with open(filepath, "wb") as af:
                af.write(part.get_payload(decode=True))
            email_data["attachments"].append({
                "name": safe_filename,
                "size": os.path.getsize(filepath),
                "hash_md5": hash_file(filepath)
            })

    return email_data

def parse_eml_folder(folder_path):
    results = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".eml"):
                filepath = os.path.join(root, file)
                try:
                    data = parse_eml_file(filepath)
                    results.append(data)
                    print(f"[OK] E-mail processado: {file}")
                except Exception as e:
                    print(f"[ERRO] Falha ao processar {file}: {e}")
    return results

def export_results(results, prefix="email_analysis"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"{prefix}_{timestamp}.json"
    csv_file = f"{prefix}_{timestamp}.csv"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    headers = ["subject", "from", "to", "cc", "bcc", "date", "message_id", "attachments"]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in results:
            r_copy = r.copy()
            r_copy["attachments"] = ", ".join([a["name"] for a in r["attachments"]])
            writer.writerow(r_copy)

    print(f"\n✅ Resultados salvos em JSON: {json_file} e CSV: {csv_file}")

if __name__ == "__main__":
    folder = input("Digite o caminho da pasta com arquivos .eml: ").strip()
    results = parse_eml_folder(folder)
    export_results(results)
