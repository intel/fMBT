fmbt_version = "0.42-0.rc0"
fmbt_build_info = "-457c35b"

import os
if os.name == "nt":
    # Python3.x _winreg renamed to winreg
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Intel fMBT", 0, winreg.KEY_ALL_ACCESS)
        fmbt_install_location = winreg.QueryValueEx(key, "InstallLocation")[0][1:-1]
    except Exception:
        fmbt_install_location = ""
    imagemagick_convert = os.path.join(fmbt_install_location, "IMconvert.exe")
else:
    fmbt_install_location = ""
    imagemagick_convert = "convert"
