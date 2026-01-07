import sys
import platform

def os_info():
    info = {
        "platform": sys.platform,
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "uname": platform.uname()._asdict(),
    }

    # Linux-specific distro info
    if info["system"] == "Linux":
        info["distro"] = {}
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.rstrip().split("=", 1)
                        info["distro"][k] = v.strip('"')
        except FileNotFoundError:
            pass

    return info

print(os_info())
