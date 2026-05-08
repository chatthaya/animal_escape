"""
stats_viewer.py  —  Animal Escape  |  Statistics Viewer
ธีมเดียวกับ main.py: Fredoka One / Baloo 2 / Nunito, wood buttons, bright palette
"""

import os, csv, math, tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec

CSV_FILE = "stats.csv"

# ══════════════════════════════════════════════════════════
#  PALETTE  (bright, game-matching)
# ══════════════════════════════════════════════════════════
C = {
    "bg":           "#2d5a1b",
    "bg_dark":      "#1e3d10",
    "bg_card":      "#264d14",
    "bg_panel":     "#1a3a0e",
    "wood_dark":    "#3d1f05",
    "wood_mid":     "#6b3a0f",
    "wood_hi":      "#a0632a",
    "wood_light":   "#c8954a",
    "text_cream":   "#fff5cc",
    "text_yellow":  "#ffe850",
    "text_green_hi":"#dcff8c",
    "text_sub":     "#b8e878",
    "gold":         "#f5c832",
    "gold_bright":  "#ffe84f",
    "green_btn":    "#3cc828",
    "green_hover":  "#50e140",
    "green_border": "#156b0e",
    "green_hi":     "#a0ff60",
    "red_btn":      "#dc3218",
    "red_hover":    "#f54628",
    "red_border":   "#781008",
    "red_hi":       "#ff7860",
    "blue":         "#4fc3f7",
    "purple":       "#ce8aee",
    "orange":       "#ffb74d",
    "teal":         "#4edbac",
    "yellow":       "#f1e040",
}

# ══════════════════════════════════════════════════════════
#  FONT  —  same candidate list as main.py
# ══════════════════════════════════════════════════════════
_FONT_CANDS = [
    "Fredoka One", "Baloo 2", "Nunito", "Varela Round",
    "Arial Rounded MT Bold", "Comic Sans MS", "Arial"
]
_font_cache = {}

def gf(size, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    import tkinter.font as tkfont
    result = ("Arial", size, "bold" if bold else "normal")
    for name in _FONT_CANDS:
        try:
            f = tkfont.Font(family=name, size=size)
            if f.actual("family") not in ("", "TkDefaultFont", "Sans"):
                result = (name, size, "bold" if bold else "normal")
                break
        except Exception:
            pass
    _font_cache[key] = result
    return result

# ══════════════════════════════════════════════════════════
#  MATPLOTLIB ITEM COLORS
# ══════════════════════════════════════════════════════════
ITEM_COLORS = {
    "heal":   "#e74c3c",
    "shield": "#4fc3f7",
    "clock":  "#ffb74d",
    "wall":   "#ce8aee",
    "trap":   "#3cc828",
    "star":   "#f1e040",
}

ZONES = {
    "Zone A\n(Top-Left)":     lambda c, r: c < 13 and r < 10,
    "Zone B\n(Top-Right)":    lambda c, r: c >= 13 and r < 10,
    "Zone C\n(Bottom-Left)":  lambda c, r: c < 13 and r >= 10,
    "Zone D\n(Bottom-Right)": lambda c, r: c >= 13 and r >= 10,
}

# ══════════════════════════════════════════════════════════
#  CSV
# ══════════════════════════════════════════════════════════
def load_csv():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

# ══════════════════════════════════════════════════════════
#  MATPLOTLIB STYLE
# ══════════════════════════════════════════════════════════
def style_ax(ax, title=""):
    ax.set_facecolor(C["bg_card"])
    ax.tick_params(colors=C["text_sub"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(C["wood_mid"])
        spine.set_linewidth(1.8)
    ax.xaxis.label.set_color(C["text_sub"])
    ax.yaxis.label.set_color(C["text_sub"])
    ax.grid(True, color="#3a6e20", alpha=0.35, linestyle="--", linewidth=0.7)
    if title:
        ax.set_title(title, color=C["gold_bright"], fontweight="bold",
                     fontsize=10, pad=7)

# ══════════════════════════════════════════════════════════
#  GRAPH BUILDERS
# ══════════════════════════════════════════════════════════
def build_pie_chart(ax, rows):
    counts = defaultdict(int)
    for r in rows:
        if r["event"] == "item_collect" and r["item_type"]:
            counts[r["item_type"].replace(".png", "")] += 1
    style_ax(ax, "Item Collection (%)")
    if not counts:
        ax.text(0.5, 0.5, "No item data yet", ha="center", va="center",
                transform=ax.transAxes, fontsize=11, color=C["text_sub"])
        return
    labels = list(counts.keys())
    sizes  = list(counts.values())
    colors = [ITEM_COLORS.get(l, "#888") for l in labels]
    _, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.1f%%",
        startangle=140, textprops={"fontsize": 9, "color": C["text_cream"]},
        wedgeprops={"linewidth": 2, "edgecolor": C["bg_dark"]}, pctdistance=0.78)
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color(C["bg_dark"])
        at.set_fontweight("bold")

def build_zone_bar(ax, rows):
    zone_counts = {z: 0 for z in ZONES}
    for r in rows:
        if r["event"] == "position":
            col   = int(safe_float(r["player_x"]) // 30)
            row_g = int(safe_float(r["player_y"]) // 30)
            for zname, fn in ZONES.items():
                if fn(col, row_g):
                    zone_counts[zname] += 1
                    break
    style_ax(ax, "Player Position by Zone")
    ax.set_xlabel("Map Zone")
    ax.set_ylabel("Frequency")
    bar_colors = [C["blue"], C["red_btn"], C["green_btn"], C["orange"]]
    bars = ax.bar(list(zone_counts.keys()), list(zone_counts.values()),
                  color=bar_colors, edgecolor=C["bg_dark"], linewidth=1.2, width=0.6)
    for bar, cnt in zip(bars, zone_counts.values()):
        if cnt > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(cnt), ha="center", va="bottom",
                    fontsize=9, color=C["gold_bright"], fontweight="bold")
    ax.tick_params(axis="x", labelsize=7)

def build_mana_line(ax, rows):
    times = [safe_float(r["survival_time"]) for r in rows if r["event"] == "position"]
    manas = [safe_float(r["mana"])          for r in rows if r["event"] == "position"]
    style_ax(ax, "Mana Usage over Time")
    ax.set_xlabel("Survival Time (sec)")
    ax.set_ylabel("Remaining Mana")
    if not times:
        ax.text(0.5, 0.5, "No mana data yet", ha="center", va="center",
                transform=ax.transAxes, fontsize=11, color=C["text_sub"])
        return
    ax.plot(times, manas, color=C["blue"], linewidth=2, alpha=0.9,
            path_effects=[pe.SimpleLineShadow(shadow_color=C["bg_dark"], alpha=0.6),
                          pe.Normal()])
    ax.fill_between(times, manas, alpha=0.22, color=C["blue"])
    ax.set_ylim(bottom=0)

def build_hp_area(ax, rows):
    evs = [(safe_float(r["survival_time"]), safe_float(r["hp"]))
           for r in rows if r["event"] in ("position", "damage", "game_over")]
    style_ax(ax, "HP over Time  (Combat & Damage)")
    ax.set_xlabel("Survival Time (sec)")
    ax.set_ylabel("Current HP")
    if not evs:
        ax.text(0.5, 0.5, "No HP data yet", ha="center", va="center",
                transform=ax.transAxes, fontsize=11, color=C["text_sub"])
        return
    evs.sort()
    times = [e[0] for e in evs]
    hps   = [e[1] for e in evs]
    ax.fill_between(times, hps, alpha=0.38, color=C["red_btn"])
    ax.plot(times, hps, color=C["red_hover"], linewidth=2,
            path_effects=[pe.SimpleLineShadow(shadow_color=C["bg_dark"], alpha=0.5),
                          pe.Normal()])
    dmg = [(safe_float(r["survival_time"]), safe_float(r["hp"]))
           for r in rows if r["event"] == "damage"]
    if dmg:
        ax.scatter([d[0] for d in dmg], [d[1] for d in dmg],
                   color=C["purple"], s=40, zorder=5, label="Damage Hit",
                   edgecolors=C["bg_dark"], linewidths=0.8, alpha=0.9)
        ax.legend(fontsize=8, facecolor=C["bg_panel"],
                  edgecolor=C["wood_mid"], labelcolor=C["text_cream"])
    ax.set_ylim(bottom=0)

def build_enemy_bar(ax, rows):
    char_dists = defaultdict(list)
    for r in rows:
        if r["event"] == "enemy_proximity":
            char_dists[r["char_type"] or "Unknown"].append(safe_float(r["enemy_dist"]))
    style_ax(ax, "Enemy Proximity\nby Character")
    ax.set_xlabel("Character Type")
    ax.set_ylabel("Avg Distance (px)")
    if not char_dists:
        ax.text(0.5, 0.5, "No proximity data\n(enemy < 100px)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=10, color=C["text_sub"])
        return
    chars = list(char_dists.keys())
    avgs  = [sum(v) / len(v) for v in char_dists.values()]
    bars = ax.bar(chars, avgs,
                  color=[C["orange"], C["purple"], C["teal"]][:len(chars)],
                  edgecolor=C["bg_dark"], linewidth=1.2, width=0.5)
    for bar, avg in zip(bars, avgs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{avg:.1f}px", ha="center", va="bottom",
                fontsize=9, color=C["gold_bright"], fontweight="bold")

# ══════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════
def build_summary(rows):
    def st(vals):
        if not vals:
            return "-", "-", "-", "-"
        s = sorted(vals)
        n = len(s)
        med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        return f"{sum(s)/n:.2f}", f"{med:.2f}", f"{max(s):.2f}", f"{min(s):.2f}"
    return [
        ("Survival Time (sec)", *st([safe_float(r["survival_time"]) for r in rows if r["event"] == "game_over"])),
        ("Remaining Mana",      *st([safe_float(r["mana"])          for r in rows if r["event"] == "position"])),
        ("Enemy Distance (px)", *st([safe_float(r["enemy_dist"])    for r in rows if r["event"] == "enemy_proximity"])),
        ("Final Score",         *st([safe_float(r["score"])         for r in rows if r["event"] == "game_over"])),
    ]

# ══════════════════════════════════════════════════════════
#  WOOD BUTTON  —  replicates main.py draw_wood_btn exactly
# ══════════════════════════════════════════════════════════
class WoodButton(tk.Canvas):
    _STYLES = {
        "green":  dict(fill=(60,200,50),  fill_h=(80,225,65),  border=(20,110,15),  hi=(160,255,120), tc=(255,255,255), oc=(20,90,10)),
        "gold":   dict(fill=(255,195,30), fill_h=(255,215,55), border=(150,90,10),  hi=(255,240,130), tc=(255,255,255), oc=(120,65,5)),
        "red":    dict(fill=(220,50,30),  fill_h=(245,70,45),  border=(120,20,10),  hi=(255,120,100), tc=(255,255,255), oc=(100,15,5)),
        "brown":  dict(fill=(195,130,50), fill_h=(215,150,65), border=(110,70,20),  hi=(230,180,110), tc=(255,245,200), oc=(80,45,10)),
        "grey":   dict(fill=(90,90,90),   fill_h=(90,90,90),   border=(55,55,55),   hi=(120,120,120), tc=(180,180,180), oc=(40,40,40)),
    }

    def __init__(self, parent, text, command=None,
                 btn_w=180, btn_h=52, style="brown",
                 font_size=14, greyed=False, bg_color=None, **kw):
        bg = bg_color or C["bg_dark"]
        super().__init__(parent, width=btn_w, height=btn_h,
                         highlightthickness=0, bg=bg, **kw)
        self.text     = text
        self.command  = command
        self.btn_w    = btn_w
        self.btn_h    = btn_h
        self.style    = "grey" if greyed else style
        self.font_sz  = font_size
        self.hovered  = False
        self.greyed   = greyed
        self._draw()
        self.bind("<Enter>",           self._enter)
        self.bind("<Leave>",           self._leave)
        self.bind("<Button-1>",        self._click)
        self.bind("<ButtonRelease-1>", self._release)

    @staticmethod
    def _hex(rgb):
        return "#%02x%02x%02x" % tuple(int(x) for x in rgb)

    def _rr(self, x0, y0, x1, y1, r, fill, outline, width=0):
        pts = [x0+r,y0, x1-r,y0, x1,y0+r, x1,y1-r,
               x1-r,y1, x0+r,y1, x0,y1-r, x0,y0+r]
        kw = dict(smooth=True, fill=self._hex(fill) if fill else "",
                  outline=self._hex(outline) if outline else "")
        if width:
            kw["width"] = width
        self.create_polygon(pts, **kw)

    def _draw(self):
        self.delete("all")
        st = self._STYLES[self.style]
        W, H = self.btn_w, self.btn_h
        fill   = st["fill_h"] if self.hovered else st["fill"]
        border = st["border"]
        hi     = st["hi"]
        tc     = st["tc"]
        oc     = st["oc"]
        r = 16

        # drop shadow
        self._rr(5, 5, W-1, H-1, r, (15,10,5), (15,10,5))
        # body
        self._rr(0, 0, W-5, H-5, r, fill, border, width=4)
        # top highlight stripe
        stripe_h = max(6, (H-5)//5)
        self._rr(10, 7, W-14, 7+stripe_h, max(r-6,4), hi, ())

        # outlined text — letter by letter (same approach as main.py)
        fn_name = gf(self.font_sz, bold=False)[0]
        font    = (fn_name, self.font_sz, "bold")
        spacing = 2
        thickness = 3

        # measure total width using temporary label
        char_ws = []
        for ch in self.text:
            tmp = tk.Label(self, text=ch, font=font)
            char_ws.append(tmp.winfo_reqwidth())
            tmp.destroy()
        total_w = sum(char_ws) + spacing * max(0, len(self.text) - 1)

        cx = (W - 5) // 2
        cy = (H - 5) // 2
        x  = cx - total_w // 2

        for ch, cw in zip(self.text, char_ws):
            mid = x + cw // 2
            for dx in range(-thickness, thickness+1):
                for dy in range(-thickness, thickness+1):
                    if dx == 0 and dy == 0:
                        continue
                    if abs(dx) + abs(dy) <= thickness + 1:
                        self.create_text(mid+dx, cy+dy, text=ch,
                                         font=font, fill=self._hex(oc), anchor="center")
            self.create_text(mid, cy, text=ch, font=font,
                             fill=self._hex(tc), anchor="center")
            x += cw + spacing

    def _enter(self, _):
        if not self.greyed:
            self.hovered = True
            self._draw()

    def _leave(self, _):
        self.hovered = False
        self._draw()

    def _click(self, _):
        if not self.greyed:
            self.move("all", 2, 2)
            self.update_idletasks()

    def _release(self, _):
        self.move("all", -2, -2)
        if self.command and not self.greyed:
            self.command()

# ══════════════════════════════════════════════════════════
#  WOOD BANNER  —  header plank like in-game UI panels
# ══════════════════════════════════════════════════════════
class WoodBanner(tk.Canvas):
    def __init__(self, parent, text, width=500, height=48,
                 bg_color=None, font_size=13, **kw):
        bg = bg_color or C["bg"]
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=bg, **kw)
        self._text  = text
        self._W     = width
        self._H     = height
        self._fsz   = font_size
        self._draw()

    @staticmethod
    def _hex(rgb):
        return "#%02x%02x%02x" % tuple(int(x) for x in rgb)

    def _rr(self, x0, y0, x1, y1, r, fill, outline, width=0):
        pts = [x0+r,y0, x1-r,y0, x1,y0+r, x1,y1-r,
               x1-r,y1, x0+r,y1, x0,y1-r, x0,y0+r]
        kw = dict(smooth=True, fill=fill, outline=outline)
        if width:
            kw["width"] = width
        self.create_polygon(pts, **kw)

    def _draw(self):
        self.delete("all")
        W, H = self._W, self._H
        r = 10
        # shadow
        self._rr(3,3,W-1,H-1,r, self._hex((15,10,5)), "", 0)
        # body
        self._rr(0,0,W-4,H-4,r, self._hex((110,58,14)), self._hex((60,30,5)), 3)
        # highlight
        self._rr(10,6,W-14,14,4, self._hex((180,110,50)), "", 0)
        # inner border
        self._rr(4,4,W-8,H-8,r-2, "", self._hex((80,45,10)), 2)

        fn = gf(self._fsz, False)[0]
        font = (fn, self._fsz, "bold")
        cx, cy = (W-4)//2, (H-4)//2
        # outline passes
        for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2),(-2,0),(2,0),(0,-2),(0,2)]:
            self.create_text(cx+dx, cy+dy, text=self._text,
                             font=font, fill="#3d1f05", anchor="center")
        self.create_text(cx, cy, text=self._text,
                         font=font, fill=C["text_cream"], anchor="center")

# ══════════════════════════════════════════════════════════
#  HEADER CANVAS  (wood plank top bar)
# ══════════════════════════════════════════════════════════
def make_header(parent, row_count):
    hdr_c = tk.Canvas(parent, height=76, highlightthickness=0,
                      bg=C["wood_dark"])
    hdr_c.pack(fill="x")

    def redraw(event=None):
        hdr_c.delete("all")
        W = hdr_c.winfo_width() or 1150
        # wood grain stripes
        for i in range(10):
            y = i * 8
            col = C["wood_mid"] if i % 2 == 0 else C["wood_dark"]
            hdr_c.create_rectangle(0, y, W, y+8, fill=col, outline="")
        # borders
        hdr_c.create_rectangle(0, 0, W, 4, fill=C["wood_light"], outline="")
        hdr_c.create_rectangle(0, 72, W, 76, fill=C["wood_dark"], outline="")

        fn_big = gf(26, False)[0]
        fn_sub = gf(12, False)[0]
        title = "ANIMAL ESCAPE"
        sub   = "STATISTICS  DASHBOARD"

        # title shadow + outline
        hdr_c.create_text(W//2+3, 26+3, text=title,
                          font=(fn_big,26,"bold"), fill="#1a0d00", anchor="center")
        for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2),(-2,0),(2,0),(0,-2),(0,2)]:
            hdr_c.create_text(W//2+dx, 26+dy, text=title,
                              font=(fn_big,26,"bold"), fill="#3d1f05", anchor="center")
        hdr_c.create_text(W//2, 26, text=title,
                          font=(fn_big,26,"bold"), fill=C["gold_bright"], anchor="center")

        # subtitle
        for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
            hdr_c.create_text(W//2+dx, 54+dy, text=sub,
                              font=(fn_sub,12,"bold"), fill="#3d1f05", anchor="center")
        hdr_c.create_text(W//2, 54, text=sub,
                          font=(fn_sub,12,"bold"), fill=C["text_sub"], anchor="center")

        # badge
        badge = f"📂  {row_count} records   |   {CSV_FILE}"
        hdr_c.create_text(W-14, 38, text=badge,
                          font=(fn_sub,9,"bold"),
                          fill=C["text_cream"], anchor="e")

    hdr_c.bind("<Configure>", redraw)
    hdr_c.after(80, redraw)
    return hdr_c

# ══════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════
def open_stats_window():
    rows = load_csv()

    root = tk.Tk()
    root.title("Animal Escape  —  Statistics")
    root.geometry("1150x860")
    root.resizable(True, True)
    root.configure(bg=C["bg_dark"])

    make_header(root, len(rows))

    # ── NOTEBOOK ──────────────────────────────────────────
    s = ttk.Style()
    s.theme_use("default")
    fn_tab = gf(10, False)[0]

    s.configure("Wood.TNotebook",
                background=C["bg_dark"], borderwidth=0, tabmargins=[6,6,0,0])
    s.configure("Wood.TNotebook.Tab",
                background=C["wood_mid"],
                foreground=C["text_cream"],
                padding=[18, 8],
                font=(fn_tab, 10, "bold"),
                borderwidth=2)
    s.map("Wood.TNotebook.Tab",
          background=[("selected", C["wood_hi"]),  ("active", C["wood_dark"])],
          foreground=[("selected", C["gold_bright"]), ("active", C["text_cream"])])

    nb = ttk.Notebook(root, style="Wood.TNotebook")
    nb.pack(fill="both", expand=True, padx=8, pady=(6,0))

    # ── helper: make a single-graph tab ──────────────────
    def make_single_graph_tab(label, banner_title, builder_fn, figsize=(11, 7)):
        tab = tk.Frame(nb, bg=C["bg_dark"])
        nb.add(tab, text=label)

        # WoodBanner title (same style as "Statistical Summary")
        WoodBanner(tab, banner_title,
                   width=520, height=48, bg_color=C["bg_dark"],
                   font_size=14).pack(pady=(14, 4))

        fig = plt.Figure(figsize=figsize, facecolor=C["bg_dark"])
        fig.subplots_adjust(left=0.10, right=0.95, top=0.96, bottom=0.12)
        ax = fig.add_subplot(111)
        builder_fn(ax, rows)
        ax.set_title("")

        fig.patch.set_linewidth(0)

        cvs = FigureCanvasTkAgg(fig, master=tab)
        cvs.draw()
        w = cvs.get_tk_widget()
        w.configure(bg=C["bg_dark"],
                    highlightbackground=C["wood_mid"], highlightthickness=3)
        w.pack(fill="both", expand=True, padx=12, pady=(4, 10))
        return tab

    # ─────────────────────────────────────────────────────
    # TAB 1 — All Graphs (overview)
    # ─────────────────────────────────────────────────────
    tab_g = tk.Frame(nb, bg=C["bg_dark"])
    nb.add(tab_g, text="  📈  All Graphs  ")

    fig = plt.Figure(figsize=(14, 9.2), facecolor=C["bg_dark"])
    fig.subplots_adjust(hspace=0.55, wspace=0.38,
                        left=0.07, right=0.97, top=0.95, bottom=0.08)
    gs  = gridspec.GridSpec(2, 3, figure=fig)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[1, 0:2])
    ax5 = fig.add_subplot(gs[1, 2])

    build_pie_chart(ax1, rows)
    build_zone_bar(ax2, rows)
    build_mana_line(ax3, rows)
    build_hp_area(ax4, rows)
    build_enemy_bar(ax5, rows)

    cvs = FigureCanvasTkAgg(fig, master=tab_g)
    cvs.draw()
    cvs.get_tk_widget().configure(bg=C["bg_dark"],
                                  highlightbackground=C["wood_mid"],
                                  highlightthickness=3)
    cvs.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=6)

    # ─────────────────────────────────────────────────────
    # TABS 2-6 — Individual graph tabs
    # ─────────────────────────────────────────────────────
    # ── Items tab (pie) — custom build with bg frame ─────
    tab_items = tk.Frame(nb, bg=C["bg_dark"])
    nb.add(tab_items, text="  🍄  Items  ")
    WoodBanner(tab_items, "🍄  Item Collection  🍄",
               width=520, height=48, bg_color=C["bg_dark"],
               font_size=14).pack(pady=(14, 4))
    # bg frame that matches the dark card color — the extra layer
    pie_bg = tk.Frame(tab_items, bg=C["bg_card"],
                      highlightbackground=C["wood_mid"], highlightthickness=3)
    pie_bg.pack(fill="both", expand=True, padx=12, pady=(4, 10))
    pie_fig = plt.Figure(figsize=(9, 7), facecolor=C["bg_card"])
    pie_fig.subplots_adjust(left=0.05, right=0.95, top=0.96, bottom=0.05)
    pie_ax = pie_fig.add_subplot(111)
    build_pie_chart(pie_ax, rows)
    pie_ax.set_title("")
    pie_ax.set_facecolor(C["bg_card"])
    pie_fig.patch.set_linewidth(0)
    pie_cvs = FigureCanvasTkAgg(pie_fig, master=pie_bg)
    pie_cvs.draw()
    pie_cvs.get_tk_widget().configure(bg=C["bg_card"], highlightthickness=0)
    pie_cvs.get_tk_widget().pack(fill="both", expand=True)
    make_single_graph_tab("  🗺️  Zones  ",       "🗺️  Player Position by Zone  🗺️",  build_zone_bar,   figsize=(9, 7))
    make_single_graph_tab("  💧  Mana  ",        "💧  Mana Usage over Time  💧",   build_mana_line,  figsize=(11, 7))
    make_single_graph_tab("  ❤️  HP / Damage  ", "❤️  HP over Time & Damage  ❤️",  build_hp_area,    figsize=(11, 7))
    make_single_graph_tab("  🐺  Enemy Prox.  ","🐺  Enemy Proximity by Character  🐺", build_enemy_bar,  figsize=(9, 7))

    # ─────────────────────────────────────────────────────
    # TAB 7 — Summary Stats
    # ─────────────────────────────────────────────────────
    tab_s = tk.Frame(nb, bg=C["bg"])
    nb.add(tab_s, text="  📋  Summary Stats  ")

    WoodBanner(tab_s, "⚔️   Statistical Summary   ⚔️",
               width=450, height=48, bg_color=C["bg"],
               font_size=14).pack(pady=(18,10))

    fn_tree = gf(11, False)[0]
    s.configure("Wood.Treeview",
                background=C["bg_card"], foreground=C["text_cream"],
                fieldbackground=C["bg_card"], font=(fn_tree, 11),
                rowheight=38, borderwidth=0)
    s.configure("Wood.Treeview.Heading",
                background=C["wood_mid"], foreground=C["gold_bright"],
                font=(fn_tree, 11, "bold"), relief="flat")
    s.map("Wood.Treeview",
          background=[("selected", C["wood_hi"])],
          foreground=[("selected", C["gold_bright"])])

    tree_wrap = tk.Frame(tab_s, bg=C["wood_mid"], padx=3, pady=3)
    tree_wrap.pack(padx=40, pady=4, fill="x")

    cols = ("Feature", "Mean", "Median", "Max", "Min")
    tree = ttk.Treeview(tree_wrap, columns=cols, show="headings",
                        height=6, style="Wood.Treeview")
    for col, w in zip(cols, [270, 120, 120, 120, 120]):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")
    for i, row in enumerate(build_summary(rows)):
        tree.insert("", "end", values=row,
                    tags=("r0" if i % 2 == 0 else "r1",))
    tree.tag_configure("r0", background=C["bg_card"])
    tree.tag_configure("r1", background=C["bg_dark"])
    tree.pack(fill="x")

    # ── HIGH SCORE BANNER ────────────────────────────────
    score_vals = [safe_float(r["score"]) for r in rows if r["event"] == "game_over"]
    high_score = int(max(score_vals)) if score_vals else 0

    # find who got the high score
    hs_char = "—"
    hs_time = "—"
    hs_ts   = "—"
    for r in rows:
        if r["event"] == "game_over" and safe_float(r["score"]) == high_score and high_score > 0:
            hs_char = r.get("char_type", "?") or "?"
            hs_time = f"{safe_float(r['survival_time']):.1f}s"
            hs_ts   = r.get("timestamp", "?")[:16]
            break

    hs_outer = tk.Frame(tab_s, bg=C["wood_dark"],
                        highlightbackground=C["gold"], highlightthickness=3)
    hs_outer.pack(padx=40, pady=(14, 6), fill="x")

    hs_inner = tk.Canvas(hs_outer, height=110, highlightthickness=0,
                         bg=C["wood_dark"])
    hs_inner.pack(fill="x")

    def draw_hs_bg(event=None):
        hs_inner.delete("all")
        W = hs_inner.winfo_width() or 900
        H = 110
        # wood grain stripes
        for i in range(14):
            y = i * 8
            col = C["wood_mid"] if i % 2 == 0 else C["wood_dark"]
            hs_inner.create_rectangle(0, y, W, y+8, fill=col, outline="")
        # gold top & bottom border
        hs_inner.create_rectangle(0, 0, W, 5,  fill=C["gold"], outline="")
        hs_inner.create_rectangle(0, H-5, W, H, fill=C["gold"], outline="")
        # star decorations
        for sx in [28, W-28]:
            for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
                hs_inner.create_text(sx+dx, H//2+dy, text="⭐",
                                     font=(gf(22,False)[0], 22), fill=C["wood_dark"])
            hs_inner.create_text(sx, H//2, text="⭐",
                                 font=(gf(22,False)[0], 22), fill=C["gold_bright"])

        fn_hd  = gf(13, False)[0]
        fn_sc  = gf(28, False)[0]
        fn_sub = gf(10, False)[0]

        # header label
        for dx, dy in [(-1,-1),(1,1)]:
            hs_inner.create_text(W//2+dx, 20+dy,
                                 text="🏆  ALL-TIME HIGH SCORE  🏆",
                                 font=(fn_hd, 13, "bold"), fill=C["wood_dark"],
                                 anchor="center")
        hs_inner.create_text(W//2, 20,
                             text="🏆  ALL-TIME HIGH SCORE  🏆",
                             font=(fn_hd, 13, "bold"), fill=C["gold_bright"],
                             anchor="center")

        # score number
        score_txt = f"{high_score:,}" if high_score > 0 else "No data yet"
        for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2)]:
            hs_inner.create_text(W//2+dx, 62+dy, text=score_txt,
                                 font=(fn_sc, 28, "bold"), fill=C["wood_dark"],
                                 anchor="center")
        hs_inner.create_text(W//2, 62, text=score_txt,
                             font=(fn_sc, 28, "bold"), fill=C["text_yellow"],
                             anchor="center")

        # sub info
        if high_score > 0:
            sub_txt = f"Character: {hs_char}   |   Survived: {hs_time}   |   {hs_ts}"
            hs_inner.create_text(W//2, 92, text=sub_txt,
                                 font=(fn_sub, 10), fill=C["text_sub"],
                                 anchor="center")

    hs_inner.bind("<Configure>", draw_hs_bg)
    hs_inner.after(100, draw_hs_bg)

    # ── info cards ───────────────────────────────────────
    sessions   = len([r for r in rows if r["event"] == "game_over"])
    chars_used = defaultdict(int)
    for r in rows:
        if r["event"] == "game_over":
            chars_used[r["char_type"]] += 1
    total_items = len([r for r in rows if r["event"] == "item_collect"])
    char_str    = "  ".join(f"{k}:{v}x" for k, v in chars_used.items()) or "—"

    card_row = tk.Frame(tab_s, bg=C["bg"])
    card_row.pack(pady=16, padx=40, fill="x")

    def make_card(parent, icon, label, value, color):
        wrap = tk.Frame(parent, bg=C["bg_card"],
                        highlightbackground=C["wood_mid"],
                        highlightthickness=3)
        wrap.pack(side="left", expand=True, fill="both", padx=10)
        fn_ic  = gf(22, False)[0]
        fn_lbl = gf(9,  False)[0]
        fn_val = gf(17, False)[0]
        tk.Label(wrap, text=icon, font=(fn_ic, 22),
                 bg=C["bg_card"]).pack(pady=(14, 2))
        tk.Label(wrap, text=label, font=(fn_lbl, 9),
                 bg=C["bg_card"], fg=C["text_sub"]).pack()
        tk.Label(wrap, text=str(value), font=(fn_val, 17, "bold"),
                 bg=C["bg_card"], fg=color).pack(pady=(2, 14))

    make_card(card_row, "🎮", "Sessions Played", sessions,    C["green_btn"])
    make_card(card_row, "🐾", "Characters Used",  char_str,   C["blue"])
    make_card(card_row, "🍄", "Items Collected",  total_items, C["gold_bright"])

    # ─────────────────────────────────────────────────────
    # TAB 8 — Raw Data
    # ─────────────────────────────────────────────────────
    tab_r = tk.Frame(nb, bg=C["bg"])
    nb.add(tab_r, text="  🗃️  Raw Data  ")

    WoodBanner(tab_r, "📜   Recent Records  (latest 200)",
               width=430, height=48, bg_color=C["bg"],
               font_size=13).pack(pady=(18, 8))

    raw_cols = ["timestamp","event","char_type","score","hp","mana",
                "player_x","player_y","enemy_dist","item_type","survival_time"]

    raw_wrap = tk.Frame(tab_r, bg=C["wood_mid"], padx=3, pady=3)
    raw_wrap.pack(fill="both", expand=True, padx=10, pady=4)

    raw_tree = ttk.Treeview(raw_wrap, columns=raw_cols, show="headings",
                             height=22, style="Wood.Treeview")
    raw_cw = {"timestamp":90,"event":105,"char_type":78,"score":62,
              "hp":58,"mana":58,"player_x":72,"player_y":72,
              "enemy_dist":82,"item_type":82,"survival_time":100}
    for col in raw_cols:
        raw_tree.heading(col, text=col)
        raw_tree.column(col, width=raw_cw.get(col, 80), anchor="center")
    sb = ttk.Scrollbar(raw_wrap, orient="vertical", command=raw_tree.yview)
    raw_tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    raw_tree.pack(fill="both", expand=True)

    for i, r in enumerate(reversed(rows[-200:])):
        raw_tree.insert("", "end",
                        values=[r.get(c, "") for c in raw_cols],
                        tags=("r0" if i % 2 == 0 else "r1",))
    raw_tree.tag_configure("r0", background=C["bg_card"])
    raw_tree.tag_configure("r1", background=C["bg_dark"])

    # ── BOTTOM BAR ────────────────────────────────────────
    bot = tk.Frame(root, bg=C["wood_dark"],
                   highlightbackground=C["wood_light"], highlightthickness=2)
    bot.pack(fill="x", side="bottom")

    btn_area = tk.Frame(bot, bg=C["wood_dark"])
    btn_area.pack(side="left", padx=12, pady=8)

    def refresh():
        root.destroy()
        open_stats_window()

    def clear_data():
        if messagebox.askyesno("Clear Data", "ลบข้อมูลสถิติทั้งหมด?"):
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                import csv as _csv
                _csv.DictWriter(f, fieldnames=[
                    "timestamp","event","char_type","score","hp","mana",
                    "player_x","player_y","enemy_x","enemy_y","enemy_dist",
                    "item_type","survival_time"]).writeheader()
            root.destroy()
            open_stats_window()

    WoodButton(btn_area, "🔄  REFRESH", command=refresh,
               btn_w=164, btn_h=48, style="green",
               font_size=13, bg_color=C["wood_dark"]).pack(side="left", padx=4)
    WoodButton(btn_area, "🗑️  CLEAR",   command=clear_data,
               btn_w=150, btn_h=48, style="red",
               font_size=13, bg_color=C["wood_dark"]).pack(side="left", padx=4)

    fn_b = gf(9, False)[0]
    tk.Label(bot,
             text="🌿  Animal Escape  |  Stats Viewer  |  stats.csv  🌿",
             bg=C["wood_dark"], fg=C["wood_light"],
             font=(fn_b, 9, "italic")).pack(side="right", padx=14)

    root.mainloop()


if __name__ == "__main__":
    open_stats_window()