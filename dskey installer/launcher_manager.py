from adb_manager import adb

DSKEY_PACKAGE = "com.dsigner.dskey"

def is_dskey_installed():
    return DSKEY_PACKAGE in adb(["shell", "pm", "list", "packages"])

def is_dskey_enabled():
    out = adb(["shell", "pm", "list", "packages", "-d"])
    return DSKEY_PACKAGE not in out

def find_launcher():
    out = adb(["shell", "cmd", "package", "resolve-activity", "--brief",
               "android.intent.action.MAIN", "android.intent.category.HOME"])
    return out.strip()

def disable_package(pkg):
    adb(["shell", "pm", "disable-user", "--user", "0", pkg])

def enable_package(pkg):
    adb(["shell", "pm", "enable", pkg])

def set_dskey_as_launcher():
    launcher = find_launcher()
    if launcher:
        disable_package(launcher)
    enable_package(DSKEY_PACKAGE)

def restore_launcher():
    launcher = find_launcher()
    enable_package(launcher)
    disable_package(DSKEY_PACKAGE)
