import threading
import tkinter as tk
from tkinter import messagebox
import subprocess
import webbrowser

from adb_manager import *
from launcher_manager import *
from downloader import download_dskey
from device_manager import device_connected, device_name

APP_VERSION = "v1.0.1"
blink = True
menu_open = False


def run_async(fn):
    threading.Thread(target=fn, daemon=True).start()


# =====================
# JANELA
# =====================
root = tk.Tk()
root.title("DSKEY")
root.geometry("560x460")
root.resizable(False, False)
root.configure(bg="#05070d")

content = tk.Frame(root, bg="#05070d")
content.pack(fill="both", expand=True)


# =====================
# OVERLAY (fecha menu)
# =====================
overlay = tk.Frame(root, bg="#000000")
overlay.place_forget()


def close_menu(event=None):
    global menu_open
    if not menu_open:
        return
    slide_menu(False)


overlay.bind("<Button-1>", close_menu)


# =====================
# SIDEBAR MENU
# =====================
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


def toggle_menu():
    slide_menu(not menu_open)


# =====================
# MENU CONTEÚDO
# =====================
tk.Label(
    menu,
    text="MENU",
    fg="#6fbaff",
    bg="#0b0f1a",
    font=("Segoe UI", 13, "bold")
).pack(pady=18)


def menu_button(text, command):
    btn = tk.Button(
        menu,
        text=text,
        command=lambda: run_async(command),
        font=("Segoe UI", 11, "bold"),
        fg="#cfd8ff",
        bg="#0b1b3a",
        activebackground="#142b5c",
        activeforeground="#ffffff",
        bd=0,
        relief="flat",
        width=24,
        height=2,
        cursor="hand2"
    )
    btn.pack(pady=6)
    return btn


# SUPORTE
menu_button(
    "📞 SUPORTE (WhatsApp)",
    lambda: webbrowser.open("https://wa.me/54997124880")
)


# INSTALAR DSKEY (APK LOCAL)
from tkinter import filedialog

def install_dskey():
    apk = filedialog.askopenfilename(
        title="Selecionar APK do DSKEY",
        filetypes=[("APK", "*.apk")]
    )
    if not apk:
        return
    try:
        subprocess.check_output(
            ["adb", "install", "-r", apk],
            stderr=subprocess.STDOUT
        )
        messagebox.showinfo("DSKEY", "DSKEY instalado com sucesso.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror(
            "Erro ao instalar DSKEY",
            e.output.decode(errors="ignore")
        )


menu_button("📦 INSTALAR DSKEY", install_dskey)


# DESINSTALAR DSKEY
def uninstall_dskey():
    if not messagebox.askyesno(
        "Desinstalar DSKEY",
        "Deseja remover o DSKEY do dispositivo conectado?"
    ):
        return
    try:
        subprocess.call(["adb", "uninstall", DSKEY_PACKAGE])
        messagebox.showinfo("DSKEY", "DSKEY removido com sucesso.")
    except:
        messagebox.showerror("Erro", "Falha ao desinstalar DSKEY.")


menu_button("🗑 DESINSTALAR DSKEY", uninstall_dskey)


# REINSTALAR ADB
menu_button(
    "🔧 REINSTALAR ADB",
    lambda: messagebox.showinfo(
        "ADB",
        "Reinstale o ADB conforme seu sistema:\n\nWindows / Linux / Mac"
    )
)


# PAINEL
menu_button(
    "🌐 PAINEL",
    lambda: webbrowser.open("https://dsignertv.com.br")
)



# =====================
# WIFI ICON
# =====================
wifi_btn = tk.Button(
    content, text="📶",
    font=("Segoe UI", 18),
    fg="#00ff9c", bg="#05070d",
    bd=0, command=lambda: run_async(toggle_wifi)
)
wifi_btn.place(x=15, y=10)


# =====================
# PERFIL ICON
# =====================
profile_btn = tk.Button(
    content, text="👤",
    font=("Segoe UI", 16),
    fg="#6fbaff", bg="#05070d",
    bd=0, command=toggle_menu
)
profile_btn.place(x=18, y=55)


# =====================
# TÍTULO
# =====================
tk.Label(
    content, text="DSKEY INSTALADOR",
    fg="#6fbaff", bg="#05070d",
    font=("Segoe UI", 16, "bold")
).pack(pady=(30, 10))


label_device = tk.Label(
    content, text="DISP: ---",
    fg="#3cff3c", bg="#05070d",
    font=("Segoe UI", 11, "bold")
)
label_device.pack(pady=10)


# =====================
# BOTÕES
# =====================
def neon_button(text, command):
    return tk.Button(
        content, text=text,
        command=lambda: run_async(command),
        font=("Segoe UI", 11, "bold"),
        fg="#cfd8ff", bg="#0b1b3a",
        activebackground="#142b5c",
        bd=2, relief="ridge",
        width=22, height=2
    )

neon_button("ATIVAR DSKEY", set_dskey_as_launcher).pack(pady=8)
neon_button("REST LAUNCHER", restore_launcher).pack(pady=8)
neon_button("BAIXAR APK", download_dskey).pack(pady=8)


# =====================
# STATUS
# =====================
status_app = tk.Label(
    content, text="🔘APP",
    fg="#00ff00", bg="#05070d",
    font=("Segoe UI", 10, "bold")
)
status_app.place(x=20, y=395)

status_launcher = tk.Label(
    content, text="🔘LAUNCHER",
    fg="#00ff00", bg="#05070d",
    font=("Segoe UI", 10, "bold")
)
status_launcher.place(x=20, y=420)

tk.Label(
    content, text=APP_VERSION,
    fg="#6f7cff", bg="#05070d",
    font=("Segoe UI", 9)
).place(x=500, y=420)


# =====================
# WIFI TCP
# =====================
def is_tcp_connected():
    try:
        out = subprocess.check_output(["adb", "devices"]).decode()
        return ":5555" in out
    except:
        return False


def toggle_wifi():
    if is_tcp_connected():
        if not messagebox.askyesno(
            "Desconectar Wi-Fi",
            "Deseja desligar a conexão TCP?\nSerá necessário usar cabo USB."
        ):
            return
        subprocess.call(["adb", "disconnect"])
        messagebox.showinfo("Wi-Fi", "Wi-Fi desligado.\nUse cabo USB.")
        return

    try:
        ip = subprocess.check_output(
            ["adb", "shell", "ip", "route"]
        ).decode().split("src ")[1].split()[0]

        subprocess.call(["adb", "tcpip", "5555"])
        subprocess.call(["adb", "connect", f"{ip}:5555"])

        messagebox.showinfo(
            "Wi-Fi",
            "Conectado via TCP.\nPode desconectar o cabo USB."
        )
    except:
        messagebox.showerror("Wi-Fi", "Falha ao conectar via TCP.")


def blink_wifi():
    global blink
    if is_tcp_connected():
        wifi_btn.config(fg="#00ff00" if blink else "#05070d")
        blink = not blink
    else:
        wifi_btn.config(fg="#00ff9c")
    root.after(600, blink_wifi)


# =====================
# LOOP
# =====================
def refresh_status():
    if not device_connected():
        label_device.config(text="DISP: ---")
        status_app.config(fg="red")
        status_launcher.config(fg="red")
        return

    label_device.config(text=f"DISP: {device_name()}")

    if not is_dskey_installed():
        status_app.config(fg="red")
    elif is_dskey_enabled():
        status_app.config(fg="#00ff00")
    else:
        status_app.config(fg="blue")

    try:
        status_launcher.config(
            fg="#00ff00" if find_launcher() else "red"
        )
    except:
        status_launcher.config(fg="red")


def loop():
    refresh_status()
    root.after(3000, loop)


blink_wifi()
loop()
root.mainloop()
