import subprocess
import os
import glob
import winreg
import psutil
import webbrowser
import pyautogui
from datetime import datetime

# ── DYNAMIC APP FINDER ─────────────────────────────────────
def find_app(app_name):
    app_lower = app_name.lower()

    # 1. Search Start Menu shortcuts (most reliable)
    start_menu_paths = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    ]

    for base in start_menu_paths:
        for root, dirs, files in os.walk(base):
            for file in files:
                if app_lower in file.lower() and file.endswith((".lnk", ".exe")):
                    return os.path.join(root, file)

    # 2. Search Windows Registry (installed apps)
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
    ]
    for reg_path in registry_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                sub_name = winreg.EnumKey(key, i)
                if app_lower in sub_name.lower():
                    sub_key  = winreg.OpenKey(key, sub_name)
                    path, _  = winreg.QueryValueEx(sub_key, "")
                    if os.path.exists(path):
                        return path
        except:
            continue

    # 3. Search common install locations
    search_dirs = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expandvars(r"%LOCALAPPDATA%"),
        os.path.expandvars(r"%APPDATA%"),
    ]
    for directory in search_dirs:
        pattern = os.path.join(directory, "**", f"*{app_name}*.exe")
        results = glob.glob(pattern, recursive=True)
        if results:
            # Return shortest path (most likely the main exe)
            return min(results, key=len)

    # 4. Try Windows shell directly as last resort
    return app_name

def open_app(app_name):
    try:
        path = find_app(app_name)
        print(f"📂 Found: {path}")
        os.startfile(path)
        return f"Opening {app_name} right away sir."
    except Exception as e:
        # Last resort — try shell command
        try:
            subprocess.Popen(["cmd", "/c", "start", app_name],
                           shell=True)
            return f"Opening {app_name} sir."
        except:
            return f"Could not find {app_name} on your system sir."

def close_app(app_name):
    closed = False
    for proc in psutil.process_iter(['name', 'pid']):
        if app_name.lower() in proc.info['name'].lower():
            proc.kill()
            closed = True
    return f"Closed {app_name} sir." if closed else f"{app_name} is not running sir."

# ── BROWSER CONTROL ────────────────────────────────────────
WEBSITES = {
    "youtube":   "https://youtube.com",
    "linkedin":  "https://linkedin.com",
    "github":    "https://github.com",
    "google":    "https://google.com",
    "netflix":   "https://netflix.com",
    "twitter":   "https://twitter.com",
    "reddit":    "https://reddit.com",
    "whatsapp":  "https://web.whatsapp.com",
    "chatgpt":   "https://chat.openai.com",
    "dinocode":  "https://dinocode.onrender.com",
}

def open_website(site_name):
    site = site_name.lower().strip()
    if site in WEBSITES:
        webbrowser.open(WEBSITES[site])
        return f"Opening {site_name} for you sir."
    elif "." in site:
        webbrowser.open(f"https://{site}")
        return f"Opening {site} sir."
    else:
        webbrowser.open(f"https://www.google.com/search?q={site}")
        return f"Searching {site_name} on Google sir."

# ── VOLUME CONTROL ─────────────────────────────────────────
def set_volume(action):
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL

        devices  = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume   = interface.QueryInterface(IAudioEndpointVolume)
        current  = volume.GetMasterVolumeLevelScalar()

        if action == "up":
            new = min(current + 0.1, 1.0)
            volume.SetMasterVolumeLevelScalar(new, None)
            return f"Volume increased to {int(new * 100)}% sir."
        elif action == "down":
            new = max(current - 0.1, 0.0)
            volume.SetMasterVolumeLevelScalar(new, None)
            return f"Volume decreased to {int(new * 100)}% sir."
        elif action == "mute":
            volume.SetMute(1, None)
            return "Muted sir."
        elif action == "unmute":
            volume.SetMute(0, None)
            return "Unmuted sir."
    except Exception as e:
        return f"Volume control error: {e}"

# ── SYSTEM STATS ───────────────────────────────────────────
def get_system_stats():
    battery = psutil.sensors_battery()
    cpu     = psutil.cpu_percent(interval=1)
    ram     = psutil.virtual_memory()
    now     = datetime.now().strftime("%I:%M %p")

    bat_status = (
        f"{int(battery.percent)}% "
        f"{'charging' if battery.power_plugged else 'on battery'}"
    ) if battery else "not available"

    return (
        f"Time: {now}. "
        f"Battery: {bat_status}. "
        f"CPU: {cpu}%. "
        f"RAM: {ram.percent}%."
    )

# ── SCREENSHOT ─────────────────────────────────────────────
def take_screenshot():
    try:
        path = os.path.join(
            os.path.expanduser("~"), "Desktop",
            f"markus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        pyautogui.screenshot(path)
        return f"Screenshot saved to your desktop sir."
    except Exception as e:
        return f"Screenshot failed: {e}"

# ── MASTER EXECUTE ─────────────────────────────────────────
def execute_command(command: dict):
    action = command.get("action", "").lower()
    target = command.get("target", "")

    if action == "open_app":       return open_app(target)
    elif action == "close_app":    return close_app(target)
    elif action == "open_website": return open_website(target)
    elif action == "volume":       return set_volume(target)
    elif action == "system_stats": return get_system_stats()
    elif action == "screenshot":   return take_screenshot()
    else:                          return None