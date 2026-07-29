import os
import shutil
import zipfile
from pathlib import Path

import requests
from rich.progress import Progress

UI_DIR = Path.home() / ".forenselab" / "ui"
UI_ZIP_URL = "https://raw.githubusercontent.com/ErickG123/devkit_forense/gh-pages/gh-pages.zip"


def is_ui_installed() -> bool:
    if not UI_DIR.exists() or not UI_DIR.is_dir():
        return False
    try:
        return any(UI_DIR.iterdir())
    except Exception:
        return False


def download_and_install_ui():
    UI_DIR.mkdir(parents=True, exist_ok=True)

    zip_path = UI_DIR / "ui_temp.zip"

    response = requests.get(UI_ZIP_URL, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("Content-Length", 0))

    with Progress() as progress:
        task = progress.add_task("[cyan]Baixando UI...", total=total_size or None)
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(UI_DIR)

    os.remove(zip_path)

    items = list(UI_DIR.iterdir())
    if len(items) == 1 and items[0].is_dir():
        sub_dir = items[0]
        for item in sub_dir.iterdir():
            shutil.move(str(item), str(UI_DIR / item.name))
        sub_dir.rmdir()
