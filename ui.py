import webview
import threading
import os
import psutil

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markus_ui.html")

class MarkusUI:
    def __init__(self):
        self.window       = None
        self.ready        = threading.Event()
        self._query_count = 0

    def _on_loaded(self):
        self.ready.set()
        threading.Thread(target=self._stats_loop, daemon=True).start()

    def _stats_loop(self):
        import time
        while True:
            try:
                cpu     = int(psutil.cpu_percent(interval=1))
                ram     = int(psutil.virtual_memory().percent)
                battery = psutil.sensors_battery()
                bat     = int(battery.percent) if battery else 0
                self.window.evaluate_js(f"updateStats({cpu}, {ram}, {bat})")
                mem_pct = min(self._query_count * 3, 100)
                self.window.evaluate_js(f"updateMemory({mem_pct})")
            except:
                pass
            time.sleep(5)

    def set_status(self, status, color="#00c8ff"):
        if not self.window: return
        self.ready.wait(timeout=5)
        try:
            self.window.evaluate_js(f"setStatus('{status}', '{color}')")
        except: pass

    def add_message(self, sender, message):
        if not self.window: return
        self.ready.wait(timeout=5)
        try:
            msg = message.replace("'", "\\'").replace("\n", " ")
            self.window.evaluate_js(f"addMessage('{sender}', '{msg}')")
            if sender == "MARKUS":
                self._query_count += 1
        except: pass

    def add_notification(self, title, sub="", ntype="info"):
        if not self.window: return
        self.ready.wait(timeout=5)
        try:
            self.window.evaluate_js(f"addNotification('{title}', '{sub}', '{ntype}')")
        except: pass

    def run(self):
        self.window = webview.create_window(
            title            = "MARKUS",
            url              = f"file:///{HTML_PATH.replace(os.sep, '/')}",
            width            = 1280,
            height           = 800,
            resizable        = True,
            fullscreen       = False,
            background_color = "#010a12",
        )
        webview.start(self._on_loaded, debug=False)

markus_ui = MarkusUI()