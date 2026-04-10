import customtkinter as ctk
import tkinter as tk
import threading
import math
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG         = "#050810"
BG2        = "#0a0e1a"
ACCENT     = "#00c8ff"
ACCENT2    = "#0066aa"
DIM        = "#0a2030"
TEXT       = "#cce8ff"
TEXT_DIM   = "#335566"
GREEN      = "#00ff88"
ORANGE     = "#ffaa00"
RED        = "#ff4455"
WHITE      = "#e8f4ff"

class MarkusUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("MARKUS — AI System")
        self.root.geometry("780x620")
        self.root.resizable(False, False)
        self.root.attributes('-fullscreen', True)    # ← full screen
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', 
          not self.root.attributes('-fullscreen'))) # ← F11 toggles it
        self.root.configure(fg_color=BG)

        self._status_text  = "STANDBY"
        self._status_color = ACCENT
        self._angle        = 0
        self._pulse        = 0.0
        self._pulse_dir    = 1
        self._running      = True

        self._build_ui()
        self._animate()

    def _build_ui(self):
        # ── TOP BAR ──────────────────────────────────────────────
        top = tk.Frame(self.root, bg=BG, height=48)
        top.pack(fill="x", padx=0, pady=0)
        top.pack_propagate(False)

        tk.Label(top, text="▸ MARKUS", font=("Courier New", 15, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left", padx=20, pady=12)

        tk.Label(top, text="PERSONAL AI SYSTEM  v1.0",
                 font=("Courier New", 9), fg=TEXT_DIM, bg=BG).pack(side="left")

        self.clock_label = tk.Label(top, text="", font=("Courier New", 10),
                                    fg=TEXT_DIM, bg=BG)
        self.clock_label.pack(side="right", padx=20)
        self._tick_clock()

        # divider
        tk.Frame(self.root, bg=ACCENT2, height=1).pack(fill="x")

        # ── MAIN BODY ────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # LEFT PANEL — HUD Canvas + stats
        left = tk.Frame(body, bg=BG, width=220)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        self.canvas = tk.Canvas(left, width=220, height=220,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(pady=(0, 10))

        # stat rows
        for label, attr in [
            ("STATUS",  "_stat_status"),
            ("SESSION", "_stat_session"),
            ("QUERIES", "_stat_queries"),
        ]:
            row = tk.Frame(left, bg=BG2, height=36)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            tk.Frame(row, bg=ACCENT2, width=3).pack(side="left", fill="y")
            tk.Label(row, text=label, font=("Courier New", 8),
                     fg=TEXT_DIM, bg=BG2, width=8, anchor="w").pack(side="left", padx=6)
            lbl = tk.Label(row, text="—", font=("Courier New", 9, "bold"),
                           fg=ACCENT, bg=BG2, anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            setattr(self, attr, lbl)

        self._stat_status.config(text="ONLINE")
        self._stat_session.config(text=time.strftime("%H:%M"))
        self._query_count  = 0

        # ESCAPE hint
        tk.Label(left, text="[ ESC ] shutdown",
                 font=("Courier New", 8), fg=TEXT_DIM, bg=BG).pack(pady=(8, 0))

        # RIGHT PANEL — conversation log + status strip
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # status strip
        strip = tk.Frame(right, bg=BG2, height=34)
        strip.pack(fill="x", pady=(0, 8))
        strip.pack_propagate(False)

        self._dot = tk.Label(strip, text="●", font=("Courier New", 12),
                             fg=ACCENT, bg=BG2)
        self._dot.pack(side="left", padx=(10, 4), pady=6)

        self._status_label = tk.Label(strip, text="STANDBY",
                                      font=("Courier New", 11, "bold"),
                                      fg=ACCENT, bg=BG2)
        self._status_label.pack(side="left")

        tk.Label(strip, text="CTRL+SPACE  activate",
                 font=("Courier New", 8), fg=TEXT_DIM, bg=BG2).pack(side="right", padx=12)

        # conversation box
        self.textbox = tk.Text(
            right,
            font=("Courier New", 12),
            bg=BG2, fg=WHITE,
            insertbackground=ACCENT,
            selectbackground=ACCENT2,
            relief="flat",
            bd=0,
            wrap="word",
            padx=12,
            pady=10,
            state="disabled",
            cursor="arrow",
        )
        self.textbox.pack(fill="both", expand=True)

        # colour tags
        self.textbox.tag_config("markus",  foreground=ACCENT,  font=("Courier New", 12, "bold"))
        self.textbox.tag_config("you",     foreground=GREEN,   font=("Courier New", 12, "bold"))
        self.textbox.tag_config("system",  foreground=TEXT_DIM,font=("Courier New", 10))
        self.textbox.tag_config("body",    foreground=WHITE,   font=("Courier New", 12))
        self.textbox.tag_config("divider", foreground=TEXT_DIM,font=("Courier New", 8))

        # bottom bar
        tk.Frame(self.root, bg=ACCENT2, height=1).pack(fill="x")
        bot = tk.Frame(self.root, bg=BG, height=28)
        bot.pack(fill="x")
        bot.pack_propagate(False)
        tk.Label(bot, text="◈  MARKUS AI  ◈  DEEPU SYSTEMS  ◈  CALGARY",
                 font=("Courier New", 8), fg=TEXT_DIM, bg=BG).pack(expand=True)

    # ── CLOCK ────────────────────────────────────────────────────
    def _tick_clock(self):
        self.clock_label.config(text=time.strftime("  %H:%M:%S  "))
        self.root.after(1000, self._tick_clock)

    # ── ANIMATION LOOP ───────────────────────────────────────────
    def _animate(self):
        if not self._running:
            return
        self._draw_hud()
        self.root.after(40, self._animate)        # ~25 fps

    def _draw_hud(self):
        c = self.canvas
        c.delete("all")
        cx, cy, r = 110, 110, 90

        # faint grid dots
        for gx in range(0, 220, 22):
            for gy in range(0, 220, 22):
                c.create_oval(gx-1, gy-1, gx+1, gy+1, fill="#0a1828", outline="")

        # outer ring
        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      outline=ACCENT2, width=1)

        # spinning arc
        self._angle = (self._angle + 3) % 360
        c.create_arc(cx-r, cy-r, cx+r, cy+r,
                     start=self._angle, extent=110,
                     outline=ACCENT, width=2, style="arc")
        c.create_arc(cx-r, cy-r, cx+r, cy+r,
                     start=self._angle+180, extent=70,
                     outline=ACCENT2, width=1, style="arc")

        # middle ring
        mr = r - 18
        c.create_oval(cx-mr, cy-mr, cx+mr, cy+mr,
                      outline=DIM, width=1)

        # pulse circle (inner)
        self._pulse += 0.06 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse_dir = 1

        pr  = 32 + int(self._pulse * 10)
        col = self._status_color
        c.create_oval(cx-pr, cy-pr, cx+pr, cy+pr,
                      outline=col, width=2)
        c.create_oval(cx-26, cy-26, cx+26, cy+26,
                      fill=self._hex_alpha(col, 0.08), outline=col, width=1)

        # centre dot
        c.create_oval(cx-4, cy-4, cx+4, cy+4, fill=col, outline="")

        # tick marks around outer ring
        for i in range(12):
            a  = math.radians(i * 30)
            x1 = cx + (r-4)  * math.cos(a)
            y1 = cy + (r-4)  * math.sin(a)
            x2 = cx + (r+4)  * math.cos(a)
            y2 = cy + (r+4)  * math.sin(a)
            col2 = ACCENT if i % 3 == 0 else TEXT_DIM
            c.create_line(x1, y1, x2, y2, fill=col2, width=1)

        # status text inside circle
        c.create_text(cx, cy + 52,
                      text=self._status_text,
                      font=("Courier New", 9, "bold"),
                      fill=self._status_color)

    def _hex_alpha(self, hex_color, alpha):
        """Approximate a colour blended toward BG by alpha."""
        def blend(a, b, t):
            return int(a + (b - a) * t)
        h = hex_color.lstrip("#")
        r1, g1, b1 = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        r2, g2, b2 = 5, 8, 16       # BG ≈ #050810
        return "#{:02x}{:02x}{:02x}".format(
            blend(r2, r1, alpha), blend(g2, g1, alpha), blend(b2, b1, alpha))

    # ── PUBLIC API ───────────────────────────────────────────────
    def set_status(self, status, color=ACCENT):
        self._status_text  = status
        self._status_color = color
        self._status_label.config(text=status, fg=color)
        self._dot.config(fg=color)
        self._stat_status.config(text=status, fg=color)
        self.root.update_idletasks()

    def add_message(self, sender, message):
        self.textbox.configure(state="normal")

        if sender == "MARKUS":
            self.textbox.insert("end", "\nMARKUS  ", "markus")
            self.textbox.insert("end", f"{message}\n", "body")
            self._query_count += 1
            self._stat_queries.config(text=str(self._query_count))
        elif sender == "YOU":
            self.textbox.insert("end", "\nYOU     ", "you")
            self.textbox.insert("end", f"{message}\n", "body")
        else:
            self.textbox.insert("end", f"\n──  {message}\n", "system")

        self.textbox.see("end")
        self.textbox.configure(state="disabled")
        self.root.update_idletasks()

    def run(self):
        self.root.mainloop()


markus_ui = MarkusUI()