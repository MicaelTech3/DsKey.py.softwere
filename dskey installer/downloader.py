import requests
from tkinter import filedialog, messagebox
import os

DSKEY_APK_URL = "https://baixar-dskey.vercel.app/dskey.apk"

def download_dskey():
    folder = filedialog.askdirectory(
        title="Escolha a pasta para salvar o DSKEY"
    )

    if not folder:
        return

    apk_path = os.path.join(folder, "dskey.apk")

    try:
        r = requests.get(DSKEY_APK_URL, stream=True, timeout=30)
        r.raise_for_status()

        with open(apk_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        messagebox.showinfo(
            "DSKEY",
            f"APK baixado com sucesso!\n\n{apk_path}"
        )

    except Exception as e:
        messagebox.showerror(
            "Erro ao baixar",
            f"Falha ao baixar o DSKEY:\n{e}"
        )
