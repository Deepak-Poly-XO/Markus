# -*- coding: utf-8 -*-

import subprocess
import os
import glob
import winreg
import psutil
import webbrowser
import pyautogui
import threading
from datetime import datetime
import pyperclip
import time

# ── APP CACHE ──────────────────────────────────────────────
app_cache = {}

def build_app_cache():
    """Runs once on startup in background thread"""
    print("🔄 Building app cache...")
    
    search_locations = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    ]

    for base in search_locations:
        for root, dirs, files in os.walk(base):
            for file in files:
                if file.endswith((".lnk", ".exe")):
                    name = file.lower().replace(".lnk","").replace(".exe","").strip()
                    app_cache[name] = os.path.join(root, file)

    print(f"✅ App cache ready — {len(app_cache)} apps indexed")

# Build cache in background so MARKUS starts instantly
threading.Thread(target=build_app_cache, daemon=True).start()

# ── DYNAMIC APP FINDER ─────────────────────────────────────
def find_app(app_name):
    app_lower = app_name.lower().strip()

    # 1. Exact match in cache
    if app_lower in app_cache:
        return app_cache[app_lower]

    # 2. Partial match in cache
    for cached_name, path in app_cache.items():
        if app_lower in cached_name:
            return path

    # 3. Registry fallback
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
                    sub_key = winreg.OpenKey(key, sub_name)
                    path, _ = winreg.QueryValueEx(sub_key, "")
                    if os.path.exists(path):
                        return path
        except:
            continue

    # 4. Last resort — shell
    return app_name

def open_and_write(app_name, text):
    try:
        import pygetwindow as gw
        import pyperclip

        # Check if app already open
        existing = [w for w in gw.getAllWindows() 
                   if app_name.lower() in w.title.lower()]

        if existing:
            # Focus existing window instead of opening new one
            print(f"📋 {app_name} already open — focusing existing window")
            win = existing[0]
            win.restore()
            win.activate()
            time.sleep(0.5)
        else:
            # Open fresh
            print(f"📂 Opening {app_name}...")
            open_app(app_name)
            time.sleep(2.5)

            windows = [w for w in gw.getAllWindows()
                      if app_name.lower() in w.title.lower()]
            if windows:
                windows[0].activate()
                time.sleep(0.5)

        # Type at current cursor position
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        print(f"✅ Written: {text[:30]}...")

        return f"Written to {app_name} sir."

    except Exception as e:
        print(f"❌ Write error: {e}")
        return f"Could not write to {app_name} sir."

def open_app(app_name):
    try:
        path = find_app(app_name)
        print(f"📂 Found: {path}")
        os.startfile(path)
        return f"Opening {app_name} right away sir."
    except Exception as e:
        try:
            subprocess.Popen(["cmd", "/c", "start", app_name], shell=True)
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

        devices   = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume    = interface.QueryInterface(IAudioEndpointVolume)
        current   = volume.GetMasterVolumeLevelScalar()

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
        from PIL import ImageGrab

        # Check OneDrive Desktop first, then standard
        onedrive_desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        standard_desktop = os.path.join(os.path.expanduser("~"), "Desktop")

        desktop = onedrive_desktop if os.path.exists(onedrive_desktop) else standard_desktop

        filename = f"markus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path     = os.path.join(desktop, filename)

        print(f"📸 Saving to: {path}")
        img = ImageGrab.grab()
        img.save(path)

        print(f"✅ Saved successfully")
        return f"Screenshot saved to your desktop sir."

    except Exception as e:
        print(f"❌ Screenshot error: {e}")
        return f"Screenshot failed sir. Check terminal."

# ── MASTER EXECUTE ─────────────────────────────────────────
def execute_command(command: dict):
    action = command.get("action", "").lower()
    target = command.get("target", "")

    if action == "open_app":        return open_app(target)
    elif action == "close_app":     return close_app(target)
    elif action == "open_website":  return open_website(target)
    elif action == "volume":        return set_volume(target)
    elif action == "system_stats":  return get_system_stats()
    elif action == "screenshot":    return take_screenshot()
    elif action == "open_and_write":
        parts    = target.split("|", 1)
        app_name = parts[0] if len(parts) > 0 else "notepad"
        text     = parts[1] if len(parts) > 1 else ""
        return open_and_write(app_name, text)
    else:                           return None

# AUTO GENERATED
def markus_search_songs_youtube():
    import webbrowser
    import time
    search_query = "popular songs 2024"
    url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
    webbrowser.open(url)
    time.sleep(2)
    return "Searched for songs on YouTube sir."


# AUTO GENERATED
def markus_search_mr_bees_youtube():
    import webbrowser
    import urllib.parse
    search_query = "Mr. Bees"
    encoded_query = urllib.parse.quote(search_query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    webbrowser.open(url)
    return "Searching for Mr. Bees on YouTube sir."



