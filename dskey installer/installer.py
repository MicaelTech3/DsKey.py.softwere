from adb_manager import run_adb
from tkinter import filedialog, messagebox

DSKEY_PACKAGE = "com.dsigner.dskey"

def is_installed():
    out = run_adb(["shell", "pm", "list", "packages"])
    return DSKEY_PACKAGE in out

def install_dskey():
    if not is_installed():
        apk = filedialog.askopenfilename(
            title="Selecione o APK DsKey",
            filetypes=[("APK", "*.apk")]
        )
        if not apk:
            return
        run_adb(["install", "-r", apk])
        messagebox.showinfo("DsKey", "APK instalado com sucesso")
    else:
        messagebox.showinfo("DsKey", "DsKey já instalado")

    from launcher_manager import activate_dskey
    activate_dskey()
    messagebox.showinfo("DsKey", "DsKey ativado como launcher")
