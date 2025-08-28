import os
import json
import csv
import platform
from datetime import datetime
import shutil

IS_WINDOWS = platform.system() == "Windows"
RECOVERY_DIR = os.path.join(os.getcwd(), "recovered_files")
os.makedirs(RECOVERY_DIR, exist_ok=True)

FILE_FILTERS = {
    "imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
    "documentos": [".txt", ".doc", ".docx", ".odt", ".json"],
    "pdfs": [".pdf"],
    "planilhas": [".xls", ".xlsx", ".ods", ".csv"]
}

ACTIVE_FILTERS = FILE_FILTERS["imagens"] + FILE_FILTERS["documentos"] + FILE_FILTERS["pdfs"] + FILE_FILTERS["planilhas"]

if IS_WINDOWS:
    try:
        import winshell
        WIN_AVAILABLE = True
    except ImportError:
        WIN_AVAILABLE = False
        print("⚠️ winshell não disponível. Módulo de recuperação Windows desativado.")
else:
    WIN_AVAILABLE = False

def filter_file(filename):
    if not ACTIVE_FILTERS:
        return True
    _, ext = os.path.splitext(filename.lower())
    return ext in ACTIVE_FILTERS

def list_deleted_files_windows():
    deleted_files = []
    if not WIN_AVAILABLE:
        return deleted_files
    try:
        for item in winshell.recycle_bin():
            try:
                original_path = item.original_filename()
                name = os.path.basename(original_path)
                if not filter_file(name):
                    continue

                deleted_files.append({
                    "original_path": original_path,
                    "recycle_path": item.filename(),
                    "name": name,
                    "deleted_time": item.recycle_date().isoformat(),
                    "hidden": False
                })
            except Exception as e:
                print(f"⚠️ Falha ao processar item da Lixeira: {e}")
        print(f"[INFO] {len(deleted_files)} arquivo(s) encontrados na Lixeira com filtro aplicado.")
    except Exception as e:
        print(f"⚠️ Erro ao acessar a Lixeira: {e}")
    return deleted_files

def recover_file_windows(file_info):
    try:
        src = file_info["recycle_path"]
        dst = os.path.join(RECOVERY_DIR, file_info["name"])
        shutil.copy2(src, dst)
        print(f"[OK] Arquivo recuperado: {file_info['name']}")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao recuperar {file_info['name']}: {e}")
        return False

try:
    import pytsk3
    PYTSK3_AVAILABLE = True
except ImportError:
    PYTSK3_AVAILABLE = False
    if not IS_WINDOWS:
        print("⚠️ pytsk3 não instalado. Recuperação Linux desativada.")

def list_deleted_files_linux(partition="/"):
    deleted_files = []
    if not PYTSK3_AVAILABLE:
        return deleted_files
    try:
        img = pytsk3.Img_Info(partition)
        fs = pytsk3.FS_Info(img)
        directory = fs.open_dir(path="/")
        for entry in directory:
            try:
                if entry.info.meta and entry.info.meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC:
                    name = entry.info.name.name.decode("utf-8")
                    if not filter_file(name):
                        continue
                    deleted_files.append({
                        "name": name,
                        "inode": entry.info.meta.addr,
                        "size": entry.info.meta.size,
                        "deleted_time": datetime.fromtimestamp(entry.info.meta.mtime).isoformat()
                    })
            except:
                continue
        print(f"[INFO] {len(deleted_files)} arquivo(s) deletados encontrados na partição {partition} com filtro aplicado.")
    except Exception as e:
        print(f"[ERRO] Não foi possível acessar a partição {partition}: {e}")
    return deleted_files

def recover_file_linux(file_info, partition="/"):
    dst = os.path.join(RECOVERY_DIR, file_info["name"])
    try:
        with open(dst, "w") as f:
            f.write("Recuperação simulada para Linux")
        print(f"[OK] Arquivo simulado recuperado: {file_info['name']}")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao recuperar {file_info['name']}: {e}")
        return False

def save_recovery_results(results, prefix="data_recovery"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"{prefix}_{timestamp}.json"
    csv_file = f"{prefix}_{timestamp}.csv"

    if not results:
        results.append({"info": "Nenhum arquivo encontrado"})

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    headers = results[0].keys()
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"\n✅ Resultados salvos em JSON: {json_file} e CSV: {csv_file}")

if __name__ == "__main__":
    recovered_results = []

    if IS_WINDOWS:
        files = list_deleted_files_windows()
        for f in files:
            status = recover_file_windows(f)
            f["recovered"] = "Sim" if status else "Falha"
            recovered_results.append(f)
    else:
        partition = input("Digite a partição ou device para recuperar arquivos (ex: /dev/sda1): ").strip()
        files = list_deleted_files_linux(partition)
        for f in files:
            status = recover_file_linux(f, partition)
            f["recovered"] = "Sim" if status else "Falha"
            recovered_results.append(f)

    save_recovery_results(recovered_results)
