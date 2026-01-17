import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, scrolledtext
import platform
import os
import zipfile
import urllib.request
import webbrowser
import re
import time
import threading

# ================= CONFIG =================

APP_VERSION = "Versão 1.0.2"

PACKAGE_DSKEY = "com.dsigner.dskey"
PACKAGE_LAUNCHER = "com.google.android.tvlauncher"

ADB_DIR = "./adb"
ADB_PATH = None
SCRCPY_PATH = None
SCRCPY_PROCESS = None
SIDEBAR_OPEN = False

CMD_PASSWORD = "1234"  # Altere esta senha conforme necessário

# ================= ADB SETUP =================

def download_adb():
    global ADB_PATH
    system = platform.system().lower()

    if system == "windows":
        url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        adb_bin = "adb.exe"
    elif system == "linux":
        url = "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
        adb_bin = "adb"
    elif system == "darwin":
        url = "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
        adb_bin = "adb"
    else:
        return False

    os.makedirs(ADB_DIR, exist_ok=True)
    zip_path = os.path.join(ADB_DIR, "platform-tools.zip")
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(ADB_DIR)

    os.remove(zip_path)
    ADB_PATH = os.path.join(ADB_DIR, "platform-tools", adb_bin)
    os.chmod(ADB_PATH, 0o755)
    return True


def setup_adb():
    global ADB_PATH
    for root, _, files in os.walk(ADB_DIR):
        if "adb" in files or "adb.exe" in files:
            ADB_PATH = os.path.join(root, "adb.exe" if os.name == "nt" else "adb")
            return True
    return download_adb()


def download_scrcpy():
    global SCRCPY_PATH
    system = platform.system().lower()
    scrcpy_dir = "./scrcpy"
    os.makedirs(scrcpy_dir, exist_ok=True)
    
    notify("Baixando scrcpy...", "#ffae00")
    
    try:
        if system == "windows":
            url = "https://github.com/Genymobile/scrcpy/releases/download/v2.3.1/scrcpy-win64-v2.3.1.zip"
            zip_path = os.path.join(scrcpy_dir, "scrcpy.zip")
            urllib.request.urlretrieve(url, zip_path)
            
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(scrcpy_dir)
            
            os.remove(zip_path)
            SCRCPY_PATH = os.path.join(scrcpy_dir, "scrcpy-win64-v2.3.1", "scrcpy.exe")
            
        elif system == "linux":
            subprocess.run(["sudo", "apt", "install", "-y", "scrcpy"], check=True)
            SCRCPY_PATH = "scrcpy"
            
        elif system == "darwin":
            subprocess.run(["brew", "install", "scrcpy"], check=True)
            SCRCPY_PATH = "scrcpy"
        
        notify("scrcpy instalado com sucesso", "lime")
        return True
    except Exception as e:
        notify("Erro ao instalar scrcpy", "red")
        return False


def check_scrcpy():
    global SCRCPY_PATH
    
    # Verifica se já existe no diretório local
    if os.path.exists("./scrcpy"):
        for root_dir, _, files in os.walk("./scrcpy"):
            if "scrcpy.exe" in files or "scrcpy" in files:
                SCRCPY_PATH = os.path.join(root_dir, "scrcpy.exe" if os.name == "nt" else "scrcpy")
                return True
    
    # Verifica se está instalado no sistema
    try:
        result = subprocess.run(["scrcpy", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            SCRCPY_PATH = "scrcpy"
            return True
    except FileNotFoundError:
        pass
    
    return False


def adb(cmd):
    if not ADB_PATH:
        return ""
    return subprocess.run(
        [ADB_PATH] + cmd,
        capture_output=True,
        text=True
    ).stdout


def adb_thread(func):
    threading.Thread(target=func, daemon=True).start()

# ================= DEVICE =================

def get_device():
    out = adb(["devices"])
    for l in out.splitlines():
        if "\tdevice" in l:
            return l.split("\t")[0]
    return None


def get_ip():
    out = adb(["shell", "ip", "addr", "show", "wlan0"])
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out)
    return m.group(1) if m else None


# ================= STATUS =================

def package_status(pkg):
    if pkg not in adb(["shell", "pm", "list", "packages", pkg]):
        return "not_found"
    if pkg in adb(["shell", "pm", "list", "packages", "-d", pkg]):
        return "disabled"
    return "enabled"


# ================= NOTIFY =================

def notify(msg, color="#1ec6ff"):
    notif.config(text=msg, fg=color)
    root.bell()
    root.after(3000, lambda: notif.config(text=""))


# ================= SCRCPY CONTROL =================

def start_scrcpy():
    global SCRCPY_PROCESS
    
    if SCRCPY_PROCESS and SCRCPY_PROCESS.poll() is None:
        notify("Controle já ativo", "#ffae00")
        return
    
    if not get_device():
        notify("Nenhum dispositivo conectado", "red")
        return
    
    # Verifica e instala scrcpy se necessário
    if not SCRCPY_PATH:
        if not check_scrcpy():
            notify("Instalando scrcpy...", "#ffae00")
            if not download_scrcpy():
                return
    
    def run():
        global SCRCPY_PROCESS
        try:
            SCRCPY_PROCESS = subprocess.Popen([SCRCPY_PATH, "--stay-awake"])
            notify("Controle remoto iniciado", "lime")
        except Exception as e:
            notify("Erro ao iniciar scrcpy", "red")
    
    adb_thread(run)


def send_back():
    if not get_device():
        notify("Nenhum dispositivo conectado", "red")
        return
    adb_thread(lambda: (
        adb(["shell", "input", "keyevent", "KEYCODE_BACK"]),
        notify("BACK enviado", "#1ec6ff")
    ))


def send_home():
    if not get_device():
        notify("Nenhum dispositivo conectado", "red")
        return
    adb_thread(lambda: (
        adb(["shell", "input", "keyevent", "KEYCODE_HOME"]),
        notify("HOME enviado", "#1ec6ff")
    ))


# ================= CMD MANUAL =================

def abrir_cmd():
    senha = simpledialog.askstring("Senha", "Digite a senha:", show='*')
    
    if senha != CMD_PASSWORD:
        notify("Senha incorreta", "red")
        return
    
    cmd_window = tk.Toplevel(root)
    cmd_window.title("CMD Manual - ADB")
    cmd_window.geometry("600x400")
    cmd_window.configure(bg="#0f111a")
    
    tk.Label(cmd_window, text="Digite os comandos ADB:", 
             fg="white", bg="#0f111a", 
             font=("Arial", 10, "bold")).pack(pady=5)
    
    output_text = scrolledtext.ScrolledText(
        cmd_window, 
        height=15, 
        bg="#1a1c24", 
        fg="lime",
        font=("Courier", 9),
        insertbackground="white"
    )
    output_text.pack(padx=10, pady=5, fill="both", expand=True)
    
    input_frame = tk.Frame(cmd_window, bg="#0f111a")
    input_frame.pack(fill="x", padx=10, pady=5)
    
    cmd_entry = tk.Entry(input_frame, bg="#2c2f3a", fg="white", 
                         font=("Arial", 10), insertbackground="white")
    cmd_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    def executar_comando():
        comando = cmd_entry.get().strip()
        if not comando:
            return
        
        output_text.insert("end", f"$ adb {comando}\n", "command")
        output_text.tag_config("command", foreground="#1ec6ff")
        
        cmd_entry.delete(0, "end")
        
        def run():
            try:
                result = subprocess.run(
                    [ADB_PATH] + comando.split(),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                output = result.stdout + result.stderr
                if output:
                    output_text.insert("end", output + "\n")
                else:
                    output_text.insert("end", "Comando executado com sucesso.\n", "success")
                    output_text.tag_config("success", foreground="lime")
            except subprocess.TimeoutExpired:
                output_text.insert("end", "ERRO: Timeout do comando\n", "error")
                output_text.tag_config("error", foreground="red")
            except Exception as e:
                output_text.insert("end", f"ERRO: {str(e)}\n", "error")
                output_text.tag_config("error", foreground="red")
            
            output_text.see("end")
        
        threading.Thread(target=run, daemon=True).start()
    
    tk.Button(input_frame, text="Executar", command=executar_comando,
              bg="#1ec6ff", fg="black", font=("Arial", 9, "bold")).pack(side="left")
    
    cmd_entry.bind("<Return>", lambda e: executar_comando())
    
    output_text.insert("end", "CMD Manual ADB - Digite os comandos sem o prefixo 'adb'\n")
    output_text.insert("end", "Exemplo: devices, shell pm list packages, etc.\n\n")


# ================= ACTIONS =================

def ativar_dskey():
    def run():
        if package_status(PACKAGE_DSKEY) == "not_found":
            notify("DSKEY não encontrado", "red")
            return
        adb(["shell", "pm", "enable", PACKAGE_DSKEY])
        adb(["shell", "monkey", "-p", PACKAGE_DSKEY,
             "-c", "android.intent.category.HOME", "1"])
        adb(["shell", "pm", "disable-user", "--user", "0", PACKAGE_LAUNCHER])
        notify("DSKEY ativado", "lime")
    adb_thread(run)


def instalar_dskey():
    apk = filedialog.askopenfilename(filetypes=[("APK", "*.apk")])
    if apk:
        adb_thread(lambda: (
            adb(["install", "-r", apk]),
            notify("DSKEY instalado", "lime")
        ))


def restaurar_launcher():
    adb_thread(lambda: (
        adb(["shell", "pm", "enable", PACKAGE_LAUNCHER]),
        adb(["shell", "pm", "disable-user", "--user", "0", PACKAGE_DSKEY]),
        notify("Launcher restaurado", "#1ec6ff")
    ))


def desinstalar_dskey():
    adb_thread(lambda: (
        adb(["uninstall", PACKAGE_DSKEY]),
        notify("DSKEY desinstalado", "red")
    ))


def ativar_tcp():
    def run():
        if not get_device():
            notify("Conecte via USB primeiro", "red")
            return
        adb(["tcpip", "5555"])
        time.sleep(1)
        ip = get_ip()
        if ip:
            adb(["connect", f"{ip}:5555"])
            notify("TCP ativado", "lime")
    adb_thread(run)


def reconnect_device():
    adb_thread(lambda: (
        adb(["disconnect"]),
        adb(["start-server"]),
        notify("Reconectando dispositivo", "#ffae00")
    ))


def abrir_config_tv():
    def run():
        adb(["shell", "am", "start", "-a", "android.settings.SETTINGS"])
        notify("Abrindo configurações", "#1ec6ff")
        time.sleep(1)
        start_scrcpy()
    adb_thread(run)


def reboot_tv():
    adb_thread(lambda: (
        adb(["reboot"]),
        notify("Reiniciando TV Box", "#ffae00")
    ))


def abrir_site():
    webbrowser.open("https://baixar-dskey.vercel.app")

# ================= SIDEBAR =================

def toggle_sidebar(event=None):
    global SIDEBAR_OPEN
    if SIDEBAR_OPEN:
        sidebar.place_forget()
        SIDEBAR_OPEN = False
    else:
        sidebar.place(x=0, y=0, height=root.winfo_height())
        SIDEBAR_OPEN = True


def close_sidebar(event):
    global SIDEBAR_OPEN
    if SIDEBAR_OPEN and event.x > 200:
        sidebar.place_forget()
        SIDEBAR_OPEN = False

# ================= UI =================

root = tk.Tk()
root.title("DSKEY Manager")
root.geometry("540x500")
root.configure(bg="#0f111a")
root.resizable(False, False)
root.bind("<Button-1>", close_sidebar)

# -------- TOP BAR --------

top = tk.Frame(root, bg="#0f111a")
top.pack(fill="x")

menu_btn = tk.Label(top, text="☰", fg="white",
                    bg="#0f111a", font=("Arial", 18))
menu_btn.pack(side="left", padx=10)
menu_btn.bind("<Button-1>", toggle_sidebar)

# -------- TITLE --------

title_label = tk.Label(
    root,
    text="Dskey Software",
    fg="#1ec6ff",
    bg="#0f111a",
    font=("Arial", 18, "bold")
)
title_label.pack(pady=(25, 10))

# -------- CENTER BUTTONS --------

center_container = tk.Frame(root, bg="#0f111a")
center_container.pack(expand=True)

btn_cfg = dict(width=34, height=2, bg="#2c2f3a", fg="white")

tk.Button(center_container, text="Ativar DSKEY",
          command=ativar_dskey, **btn_cfg).pack(pady=6)

tk.Button(center_container, text="Instalar DSKEY",
          command=instalar_dskey, **btn_cfg).pack(pady=6)

tk.Button(center_container, text="Restaurar Launcher",
          command=restaurar_launcher, **btn_cfg).pack(pady=6)

# -------- BOTTOM STATUS --------

bottom_container = tk.Frame(root, bg="#0f111a")
bottom_container.pack(side="bottom", pady=10)

device_label = tk.Label(
    bottom_container,
    text="DEVICE: nenhum",
    fg="red",
    bg="#0f111a",
    font=("Arial", 10, "bold")
)
device_label.pack(pady=3)

status_frame = tk.Frame(bottom_container, bg="#0f111a")
status_frame.pack(pady=3)

tk.Label(status_frame, text="DSKEY", fg="white",
         bg="#0f111a").pack(side="left", padx=6)

dskey_dot = tk.Label(status_frame, text="●",
                     fg="red", bg="#0f111a", font=("Arial", 10, "bold"))
dskey_dot.pack(side="left", padx=6)

tk.Label(status_frame, text="LAUNCHER", fg="white",
         bg="#0f111a").pack(side="left", padx=6)

launcher_dot = tk.Label(status_frame, text="●",
                        fg="red", bg="#0f111a", font=("Arial", 10, "bold"))
launcher_dot.pack(side="left", padx=6)

tk.Label(bottom_container, text=APP_VERSION,
         fg="#666", bg="#0f111a",
         font=("Arial", 8)).pack(pady=5)

notif = tk.Label(root, text="", bg="#0f111a",
                 fg="#1ec6ff", font=("Arial", 10, "bold"))
notif.pack(side="bottom")

# -------- SIDEBAR --------

sidebar = tk.Frame(root, width=200, bg="#10121a")

def sb_btn(text, cmd):
    tk.Button(sidebar, text=text, command=cmd,
              bg="#10121a", fg="white",
              relief="flat", anchor="w").pack(fill="x", pady=6, padx=10)

sb_btn("📡 TCP", ativar_tcp)
sb_btn("📥 Baixar DSKEY", abrir_site)
sb_btn("🔄 Reconectar dispositivo", reconnect_device)
sb_btn("🗑️ Desinstalar DSKEY", desinstalar_dskey)
sb_btn("⚙️ Configurações da TV", abrir_config_tv)
sb_btn("🎮 Iniciar Controle Remoto", start_scrcpy)
sb_btn("◀️ BACK", send_back)
sb_btn("🏠 HOME", send_home)
sb_btn("💻 CMD Manual", abrir_cmd)
sb_btn("⏻ Reboot TV Box", reboot_tv)

# ================= LOOP =================

def update_status():
    device = get_device()
    if device:
        device_label.config(text=f"DEVICE: {device}", fg="lime")
    else:
        device_label.config(text="DEVICE: nenhum", fg="red")

    ds = package_status(PACKAGE_DSKEY)
    ln = package_status(PACKAGE_LAUNCHER)

    dskey_dot.config(
        fg="lime" if ds == "enabled"
        else "#1ec6ff" if ds == "disabled"
        else "red"
    )

    launcher_dot.config(
        fg="lime" if ln == "enabled"
        else "#1ec6ff" if ln == "disabled"
        else "red"
    )

    root.after(3000, update_status)

# ================= START =================

if setup_adb():
    adb(["start-server"])
    check_scrcpy()
    update_status()
else:
    device_label.config(text="ADB ERRO", fg="red")

root.mainloop()