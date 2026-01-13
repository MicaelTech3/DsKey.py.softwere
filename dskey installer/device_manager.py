from adb_manager import adb

def device_connected():
    output = adb(["devices"])
    lines = output.strip().splitlines()

    if len(lines) <= 1:
        return False

    for line in lines[1:]:
        if "\tdevice" in line:
            return True

    return False


def device_name():
    output = adb(["shell", "getprop", "ro.product.model"])
    return output.strip() if output else "Desconhecido"
