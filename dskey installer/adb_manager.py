import subprocess

ADB_PATH = r"C:\Users\micaelmac\Downloads\platform-tools-latest-windows\platform-tools\adb.exe"

def adb(cmd):
    try:
        return subprocess.check_output(
            [ADB_PATH] + cmd,
            stderr=subprocess.STDOUT,
            shell=False
        ).decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8", errors="ignore")
