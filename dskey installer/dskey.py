# =====================================================
# DSKEY – INSTALADOR E GERENCIADOR DE LAUNCHER
# ARQUIVO ÚNICO | LAYOUT PRESERVADO
# =====================================================

import os
import sys
import platform
import zipfile
import urllib.request
import stat
import threading
import subprocess
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog
import re

# =====================================================
# CONFIGURAÇÕES GERAIS
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADB_DIR = os.path.join(BASE_DIR, "platform-tools")

SYSTEM = platform.system().lower()


DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(BASE_DIR, "config_admin.txt")

FILE_MANAGER_PKG = "com.alphainventor.filemanager"

if SYSTEM == "windows":
    ADB_NAME = "adb.exe"
    ADB_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
elif SYSTEM == "linux":
    ADB_NAME = "adb"
    ADB_URL = "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
else:
    messagebox.showerror("Erro", "Sistema operacional não suportado")
    sys.exit(1)

ADB_PATH = os.path.join(ADB_DIR, ADB_NAME)

APP_VERSION = "v1.0.2"
blink = True
menu_open = False

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

DSKEY_PKG = "com.dsigner.dskey"

# URLs e Packages Padrão
DEFAULT_UPDATE_URL = "https://atualizacao-dskey.vercel.app"
DEFAULT_DSKEY_URL = "https://baixar-dskey.vercel.app"
DEFAULT_DSKEY_PKG = "com.dsigner.dskey"

# Carrega configurações personalizadas
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = {}
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        config[key] = value
                return config
        except:
            pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        return True
    except:
        return False

config = load_config()
UPDATE_URL = config.get("UPDATE_URL", DEFAULT_UPDATE_URL)
DSKEY_DOWNLOAD_URL = config.get("DSKEY_URL", DEFAULT_DSKEY_URL)
DSKEY_PKG = config.get("DSKEY_PKG", DEFAULT_DSKEY_PKG)

# =====================================================
# ADB UTIL
# =====================================================

def adb_ok():
    return os.path.exists(ADB_PATH)

def find_adb():
    for root, _, files in os.walk(ADB_DIR):
        if ADB_NAME in files:
            return os.path.join(root, ADB_NAME)
    return None

def download_adb(update):
    os.makedirs(ADB_DIR, exist_ok=True)
    zip_path = os.path.join(ADB_DIR, "platform-tools.zip")

    update(f"Baixando ADB para seu sistema ({SYSTEM})")
    urllib.request.urlretrieve(ADB_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(ADB_DIR)

    os.remove(zip_path)

    adb_real = find_adb()
    if not adb_real:
        raise RuntimeError("ADB não encontrado após extração")

    global ADB_PATH
    ADB_PATH = adb_real

    if SYSTEM == "linux":
        os.chmod(ADB_PATH, os.stat(ADB_PATH).st_mode | stat.S_IEXEC)

def adb(cmd):
    return subprocess.call(
        [ADB_PATH] + cmd,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW
    )

def adb_out(cmd):
    return subprocess.check_output(
        [ADB_PATH] + cmd,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW
    ).decode(errors="ignore")

# =====================================================
# DEVICE
# =====================================================

def device_connected():
    try:
        return len(adb_out(["devices"]).strip().splitlines()) > 1
    except:
        return False

def device_name():
    try:
        return adb_out(["shell", "getprop", "ro.product.model"]).strip()
    except:
        return "---"

# =====================================================
# LAUNCHER CONTROLE (NOVO)
# =====================================================

def get_current_launcher():
    try:
        out = adb_out([
            "shell", "cmd", "package", "resolve-activity",
            "--brief", "android.intent.action.MAIN",
            "android.intent.category.HOME"
        ])
        return out.strip()
    except:
        return None

def disable_other_launchers():
    try:
        out = adb_out([
            "shell", "cmd", "package", "query-activities",
            "-a", "android.intent.action.MAIN",
            "-c", "android.intent.category.HOME"
        ])

        for line in out.splitlines():
            if "packageName=" in line:
                pkg = line.split("packageName=")[1].strip()
                if pkg != DSKEY_PKG:
                    adb([
                        "shell", "pm", "disable-user",
                        "--user", "0", pkg
                    ])
    except:
        pass

def set_dskey_as_launcher():
    if not device_connected():
        messagebox.showwarning("DSKEY", "Nenhum dispositivo conectado.")
        return

    try:
        disable_other_launchers()

        adb(["shell", "pm", "enable", DSKEY_PKG])
        adb(["shell", "cmd", "package", "clear", DSKEY_PKG])

        adb([
            "shell", "monkey",
            "-p", DSKEY_PKG,
            "-c", "android.intent.category.HOME", "1"
        ])

        messagebox.showinfo(
            "DSKEY",
            "DSKEY definido como launcher padrão.\n\nEle abrirá automaticamente ao ligar o dispositivo."
        )

    except Exception as e:
        messagebox.showerror("Erro", str(e))

def restore_launcher():
    adb(["shell", "pm", "enable", "com.google.android.tvlauncher"])
    messagebox.showinfo("DSKEY", "Launcher original restaurado.")

# =====================================================
# APK - NOVA FUNÇÃO UNIVERSAL
# =====================================================

def get_package_name_from_apk(apk_path):
    """Extrai o package name do APK usando aapt ou método alternativo via ADB"""
    try:
        # Método 1: Usando aapt local
        aapt_path = os.path.join(os.path.dirname(ADB_PATH), "aapt")
        if SYSTEM == "windows":
            aapt_path += ".exe"
        
        if os.path.exists(aapt_path):
            result = subprocess.check_output(
                [aapt_path, "dump", "badging", apk_path],
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW
            ).decode(errors="ignore")
            
            match = re.search(r"package: name='([^']+)'", result)
            if match:
                return match.group(1)
    except:
        pass
    
    try:
        # Método 2: Usando ADB para obter info do APK após instalação
        # Obtém lista de pacotes instalados recentemente
        result = adb_out(["shell", "pm", "list", "packages", "-3"])
        packages = [line.replace("package:", "").strip() for line in result.splitlines() if line.strip()]
        
        # Retorna o último pacote instalado (mais recente)
        if packages:
            return packages[-1]
    except:
        pass
    
    return None

def download_and_install_universal_apk():
    """Baixa APK, permite seleção e instala na TV Box"""
    if not device_connected():
        messagebox.showwarning("DSKEY", "Nenhuma TV Box conectada.")
        return

    url = "https://apks.39b7cb94d40914bac590886981b0ed6e.r2.cloudflarestorage.com/com.alphainventor.filemanager/3.6.7/Gerenciador_Arquivos.apk"
    apk_path = os.path.join(DOWNLOADS_DIR, "Gerenciador_Arquivos.apk")

    try:
        messagebox.showinfo(
            "DSKEY",
            "Baixando APK...\n\nAguarde alguns segundos."
        )
        
        urllib.request.urlretrieve(url, apk_path)

        if SYSTEM == "windows":
            os.startfile(DOWNLOADS_DIR)
        else:
            subprocess.Popen(["xdg-open", DOWNLOADS_DIR])

        messagebox.showinfo(
            "DSKEY",
            "APK baixado com sucesso!\n\nSelecione o APK para instalar na TV Box."
        )

        selected_apk = filedialog.askopenfilename(
            initialdir=DOWNLOADS_DIR,
            title="Selecione o APK para instalar",
            filetypes=[("APK", "*.apk")]
        )

        if not selected_apk:
            return

        messagebox.showinfo(
            "DSKEY",
            "Instalando APK na TV Box...\n\nAguarde."
        )

        result = adb(["install", "-r", selected_apk])

        if result == 0:
            pkg_name = get_package_name_from_apk(selected_apk)
            
            if pkg_name:
                try:
                    adb([
                        "shell", "monkey",
                        "-p", pkg_name,
                        "-c", "android.intent.category.LAUNCHER",
                        "1"
                    ])
                    
                    messagebox.showinfo(
                        "DSKEY",
                        f"Aplicativo instalado com sucesso!\n\nAbrindo {pkg_name} na TV Box."
                    )
                except:
                    messagebox.showinfo(
                        "DSKEY",
                        "Aplicativo instalado com sucesso!\n\nAbra manualmente na TV Box."
                    )
            else:
                messagebox.showinfo(
                    "DSKEY",
                    "Aplicativo instalado com sucesso!\n\nAbra manualmente na TV Box."
                )
        else:
            messagebox.showerror(
                "Erro",
                "Falha ao instalar o APK.\n\nVerifique a conexão com a TV Box."
            )

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar APK:\n\n{str(e)}")


def download_dskey():
    webbrowser.open("https://baixar-dskey.vercel.app")
   

def install_dskey():
    apk = filedialog.askopenfilename(filetypes=[("APK", "*.apk")])
    if apk:
        adb(["install", "-r", apk])
        messagebox.showinfo("DSKEY", "DSKEY instalado com sucesso.")

def uninstall_dskey():
    if messagebox.askyesno("DSKEY", "Deseja desinstalar o DSKEY?"):
        adb(["uninstall", DSKEY_PKG])

# =====================================================
# WIFI ADB
# =====================================================

def is_tcp():
    try:
        return ":5555" in adb_out(["devices"])
    except:
        return False

def toggle_wifi():
    try:
        if is_tcp():
            adb(["disconnect"])
            return
        ip = adb_out(["shell", "ip", "route"]).split("src ")[1].split()[0]
        adb(["tcpip", "5555"])
        adb(["connect", f"{ip}:5555"])
    except:
        pass

# =====================================================
# LOADING
# =====================================================

class Loading(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.configure(bg="#05070d")
        self.geometry("360x180")
        self.resizable(False, False)
        self.title("DSKEY")

        self.label = tk.Label(self, text="Iniciando...",
                              fg="#6fbaff", bg="#05070d",
                              font=("Segoe UI", 12, "bold"))
        self.label.pack(pady=30)

        self.spin = tk.Label(self, text="⠋",
                             fg="#00ff9c", bg="#05070d",
                             font=("Consolas", 26))
        self.spin.pack()

        self.frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        self.i = 0
        self.running = True

        self.after(100, self.animate)
        threading.Thread(target=self.worker, daemon=True).start()

    def animate(self):
        if self.running:
            self.spin.config(text=self.frames[self.i])
            self.i = (self.i + 1) % len(self.frames)
            self.after(100, self.animate)

    def worker(self):
        try:
            if not adb_ok():
                download_adb(lambda t: self.after(0, lambda: self.label.config(text=t)))
        except Exception as e:
            def show_and_exit():
                try:
                    messagebox.showerror("Erro", str(e))
                finally:
                    self.root.quit()
                    self.root.destroy()

            self.after(0, show_and_exit)
            return

        self.after(0, self.finish)

    def finish(self):
        self.running = False
        self.destroy()
        self.root.deiconify()

# =====================================================
# UI
# =====================================================

root = tk.Tk()
root.withdraw()
root.title("DSKEY")
root.geometry("560x460")
root.configure(bg="#05070d")
root.resizable(False, False)

content = tk.Frame(root, bg="#05070d")
content.pack(fill="both", expand=True)

overlay = tk.Frame(root, bg="#000000")
overlay.place_forget()

MENU_WIDTH = 260
menu = tk.Frame(root, bg="#0b0f1a", width=MENU_WIDTH, height=460)
menu.place(x=-MENU_WIDTH, y=0)

def slide_menu(opening):
    global menu_open
    x = menu.winfo_x()
    if opening:
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        if x < 0:
            menu.place(x=min(x + 20, 0), y=0)
            root.after(8, lambda: slide_menu(True))
        else:
            menu_open = True
    else:
        if x > -MENU_WIDTH:
            menu.place(x=max(x - 20, -MENU_WIDTH), y=0)
            root.after(8, lambda: slide_menu(False))
        else:
            overlay.place_forget()
            menu_open = False

overlay.bind("<Button-1>", lambda e: slide_menu(False))

def toggle_menu():
    slide_menu(not menu_open)

def check_update():
    webbrowser.open(UPDATE_URL)
def open_admin_config():
    webbrowser.open(CONFIG_FILE if os.path.exists(CONFIG_FILE) else BASE_DIR)

# =====================================================
# COMPONENTES VISUAIS
# =====================================================

tk.Label(menu, text="MENU", fg="#6fbaff", bg="#0b0f1a",
         font=("Segoe UI", 13, "bold")).pack(pady=18)

def menu_btn(text, cmd):
    tk.Button(menu, text=text, command=cmd,
              font=("Segoe UI", 11, "bold"),
              fg="#cfd8ff", bg="#0b1b3a",
              activebackground="#142b5c",
              bd=0, width=24, height=2).pack(pady=6)

menu_btn("📦 INSTALAR DSKEY", install_dskey)
menu_btn("🗑 DESINSTALAR DSKEY", uninstall_dskey)
menu_btn("📞 SUPORTE (WhatsApp)", lambda: webbrowser.open("https://wa.me/54997124880"))
menu_btn("🌐 PAINEL", lambda: webbrowser.open("https://dsignertv.com.br"))
menu_btn("🔄 ATUALIZAÇÃO", check_update)
menu_btn("⚙️ CONFIG ADM", open_admin_config)


tk.Button(content, text="📶", font=("Segoe UI", 18),
          fg="#00ff9c", bg="#05070d", bd=0,
          command=toggle_wifi).place(x=15, y=10)

tk.Button(content, text="👤", font=("Segoe UI", 16),
          fg="#6fbaff", bg="#05070d", bd=0,
          command=toggle_menu).place(x=18, y=55)

tk.Label(content, text="DSKEY INSTALADOR",
         fg="#6fbaff", bg="#05070d",
         font=("Segoe UI", 16, "bold")).pack(pady=(30,10))

label_device = tk.Label(content, text="DISP: ---",
                        fg="#3cff3c", bg="#05070d",
                        font=("Segoe UI", 11, "bold"))
label_device.pack(pady=10)

def neon(text, cmd):
    tk.Button(content, text=text, command=cmd,
              font=("Segoe UI", 11, "bold"),
              fg="#cfd8ff", bg="#0b1b3a",
              activebackground="#142b5c",
              bd=2, relief="ridge",
              width=22, height=2).pack(pady=8)

neon("ATIVAR DSKEY", set_dskey_as_launcher)
neon("REST LAUNCHER", restore_launcher)
neon("BAIXAR APK", download_dskey)

tk.Label(content, text="🔘APP", fg="#00ff00",
         bg="#05070d", font=("Segoe UI", 10, "bold")).place(x=20, y=395)

tk.Label(content, text="🔘LAUNCHER", fg="#00ff00",
         bg="#05070d", font=("Segoe UI", 10, "bold")).place(x=20, y=420)

tk.Label(content, text=APP_VERSION,
         fg="#6f7cff", bg="#05070d",
         font=("Segoe UI", 9)).place(x=500, y=420)

def refresh():
    label_device.config(
        text=f"DISP: {device_name()}" if device_connected() else "DISP: ---"
    )
    root.after(3000, refresh)

refresh()

# =====================================================
# START
# =====================================================

Loading(root)
root.mainloop()