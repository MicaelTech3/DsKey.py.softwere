import tkinter as tk
from tkinter import messagebox, filedialog
from adb_manager import check_adb, download_adb
from device_manager import get_device
from installer import install_dskey, activate_dskey, restore_launcher
from launcher_manager import connect_tcp

class DsKeyInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DsKey Installer")
        self.geometry("500x420")
        self.resizable(False, False)

        self.label = tk.Label(self, text="DsKey Installer", font=("Arial", 18))
        self.label.pack(pady=20)

        if not check_adb():
            if messagebox.askyesno("ADB", "ADB não encontrado. Deseja baixar automaticamente?"):
                download_adb()

        self.device_btn = tk.Button(self, text="Detectar Dispositivo", command=self.detect_device)
        self.device_btn.pack(pady=10)

        self.tcp_btn = tk.Button(self, text="Conectar TCP", state="disabled", command=connect_tcp)
        self.tcp_btn.pack(pady=5)

        self.install_btn = tk.Button(self, text="Ativar DsKey", state="disabled", command=install_dskey)
        self.install_btn.pack(pady=5)

        self.restore_btn = tk.Button(self, text="Restaurar Launcher", state="disabled", command=restore_launcher)
        self.restore_btn.pack(pady=5)

    def detect_device(self):
        device = get_device()
        if not device:
            messagebox.showwarning("Dispositivo", "Nenhum dispositivo detectado.\nAtive ADB.")
        else:
            messagebox.showinfo("Dispositivo", f"Dispositivo conectado:\n{device}")
            self.tcp_btn.config(state="normal")
            self.install_btn.config(state="normal")
            self.restore_btn.config(state="normal")

if __name__ == "__main__":
    DsKeyInstaller().mainloop()
