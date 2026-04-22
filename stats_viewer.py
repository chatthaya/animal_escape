"""
stats_viewer.py
เปิด Tkinter window แสดงกราฟสถิติการเล่นทั้งหมดตาม Proposal:
  1. Item Collection      → Pie Chart
  2. Player Position Zone → Bar Chart
  3. Mana Usage           → Line Graph
  4. Combat & Damage      → Stacked Area Chart (HP over time)
  5. Enemy Proximity      → Bar Chart (Character Type vs Avg Distance)
  + ตาราง Summary Statistics (Mean, Median, Max, Min)
"""

import os
import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec

CSV_FILE = "stats.csv"

# แบ่งแผนที่เป็น 4 โซน (col, row grid 26x20)
ZONES = {
    "Zone A\n(Top-Left)":     lambda c, r: c < 13 and r < 10,
    "Zone B\n(Top-Right)":    lambda c, r: c >= 13 and r < 10,
    "Zone C\n(Bottom-Left)":  lambda c, r: c < 13 and r >= 10,
    "Zone D\n(Bottom-Right)": lambda c, r: c >= 13 and r >= 10,
}

ITEM_COLORS = {
    "heal":   "#e74c3c",
    "shield": "#3498db",
    "clock":  "#f39c12",
    "wall":   "#8e44ad",
    "trap":   "#27ae60",
    "star":   "#f1c40f",
    "trap.png": "#27ae60",
    "heal.png": "#e74c3c",
    "shield.png": "#3498db",
    "clock.png":  "#f39c12",
    "wall.png":   "#8e44ad",
    "star.png":   "#f1c40f",
}

# ---- Data Loading ----

def load_csv():
    """โหลด CSV และคืนเป็น list of dict"""
    if not os.path.exists(CSV_FILE):
        return []
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def safe_float(v, default=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


# ---- Graph Builders ----

def build_pie_chart(ax, rows):
    """1. Item Collection Pie Chart"""
    counts = defaultdict(int)
    for r in rows:
        if r["event"] == "item_collect" and r["item_type"]:
            it = r["item_type"].replace(".png", "")
            counts[it] += 1

    if not counts:
        ax.text(0.5, 0.5, "No item data yet", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray")
        ax.set_title("Item Collection", fontweight="bold")
        return

    labels = list(counts.keys())
    sizes  = list(counts.values())
    colors = [ITEM_COLORS.get(lb, "#95a5a6") for lb in labels]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors,
        autopct="%1.1f%%", startangle=140,
        textprops={"fontsize": 9}
    )
    for at in autotexts:
        at.set_fontsize(8)
    ax.set_title("Item Collection (%)", fontweight="bold")


def build_zone_bar(ax, rows):
    """2. Player Position by Zone Bar Chart"""
    zone_counts = {z: 0 for z in ZONES}
    for r in rows:
        if r["event"] == "position":
            px = safe_float(r["player_x"])
            py = safe_float(r["player_y"])
            col = int(px // 30)
            row_g = int(py // 30)
            for zname, func in ZONES.items():
                if func(col, row_g):
                    zone_counts[zname] += 1
                    break

    zones  = list(zone_counts.keys())
    counts = list(zone_counts.values())
    bars = ax.bar(zones, counts, color=["#3498db","#e74c3c","#2ecc71","#f39c12"],
                  edgecolor="white", linewidth=0.8)
    ax.set_title("Player Position by Zone", fontweight="bold")
    ax.set_xlabel("Map Zone")
    ax.set_ylabel("Frequency (count)")
    for bar, cnt in zip(bars, counts):
        if cnt > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    str(cnt), ha="center", va="bottom", fontsize=9)
    ax.tick_params(axis='x', labelsize=7)


def build_mana_line(ax, rows):
    """3. Mana Usage Line Graph"""
    times = []
    manas = []
    for r in rows:
        if r["event"] == "position":
            times.append(safe_float(r["survival_time"]))
            manas.append(safe_float(r["mana"]))

    if not times:
        ax.text(0.5, 0.5, "No mana data yet", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray")
        ax.set_title("Mana Usage over Time", fontweight="bold")
        return

    ax.plot(times, manas, color="#3498db", linewidth=1.5, alpha=0.85)
    ax.fill_between(times, manas, alpha=0.15, color="#3498db")
    ax.set_title("Mana Usage over Time", fontweight="bold")
    ax.set_xlabel("Survival Time (sec)")
    ax.set_ylabel("Remaining Mana")
    ax.set_ylim(bottom=0)


def build_hp_area(ax, rows):
    """4. Combat & Damage — HP over Time (Area Chart)"""
    times = []
    hps   = []
    # ใช้ทั้ง position + damage events เพื่อให้เห็นการตก
    for r in rows:
        if r["event"] in ("position", "damage", "game_over"):
            times.append(safe_float(r["survival_time"]))
            hps.append(safe_float(r["hp"]))

    if not times:
        ax.text(0.5, 0.5, "No HP data yet", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray")
        ax.set_title("HP over Time (Combat & Damage)", fontweight="bold")
        return

    # เรียงตามเวลา
    paired = sorted(zip(times, hps))
    times = [p[0] for p in paired]
    hps   = [p[1] for p in paired]

    ax.fill_between(times, hps, alpha=0.4, color="#e74c3c")
    ax.plot(times, hps, color="#c0392b", linewidth=1.5)
    ax.set_title("HP over Time (Combat & Damage)", fontweight="bold")
    ax.set_xlabel("Survival Time (sec)")
    ax.set_ylabel("Current HP")
    ax.set_ylim(bottom=0)

    # จุดที่โดนดาเมจ
    dmg_t = [safe_float(r["survival_time"]) for r in rows if r["event"] == "damage"]
    dmg_h = [safe_float(r["hp"]) for r in rows if r["event"] == "damage"]
    if dmg_t:
        ax.scatter(dmg_t, dmg_h, color="#8e44ad", s=25, zorder=5,
                   label="Damage Hit", alpha=0.8)
        ax.legend(fontsize=8)


def build_enemy_proximity_bar(ax, rows):
    """5. Enemy Proximity Bar Chart — Character Type vs Avg Distance"""
    char_dists = defaultdict(list)
    for r in rows:
        if r["event"] == "enemy_proximity":
            ct = r["char_type"] or "Unknown"
            char_dists[ct].append(safe_float(r["enemy_dist"]))

    if not char_dists:
        ax.text(0.5, 0.5, "No proximity data yet\n(enemy must be within 100px)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=10, color="gray")
        ax.set_title("Enemy Proximity by Character", fontweight="bold")
        return

    chars = list(char_dists.keys())
    avgs  = [sum(v)/len(v) for v in char_dists.values()]
    colors = ["#e67e22","#9b59b6","#1abc9c"]
    bars = ax.bar(chars, avgs, color=colors[:len(chars)], edgecolor="white")
    ax.set_title("Enemy Proximity by Character\n(Avg Distance when < 100px)",
                 fontweight="bold")
    ax.set_xlabel("Character Type")
    ax.set_ylabel("Avg Distance (px)")
    for bar, avg in zip(bars, avgs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{avg:.1f}px", ha="center", va="bottom", fontsize=9)


# ---- Summary Stats Table ----

def build_summary(rows):
    """คำนวณ Mean, Median, Max, Min ของ 4 features หลัก"""
    def stats(vals):
        if not vals:
            return "-", "-", "-", "-"
        s = sorted(vals)
        n = len(s)
        mean = sum(s) / n
        median = s[n//2] if n % 2 == 1 else (s[n//2-1]+s[n//2])/2
        return f"{mean:.2f}", f"{median:.2f}", f"{max(s):.2f}", f"{min(s):.2f}"

    survival_times = [safe_float(r["survival_time"]) for r in rows if r["event"] == "game_over"]
    manas          = [safe_float(r["mana"]) for r in rows if r["event"] == "position"]
    dists          = [safe_float(r["enemy_dist"]) for r in rows if r["event"] == "enemy_proximity"]
    scores         = [safe_float(r["score"]) for r in rows if r["event"] == "game_over"]

    table = [
        ("Survival Time (sec)",   *stats(survival_times)),
        ("Remaining Mana",        *stats(manas)),
        ("Enemy Distance (px)",   *stats(dists)),
        ("Final Score",           *stats(scores)),
    ]
    return table


# ---- Main Tkinter Window ----

def open_stats_window():
    rows = load_csv()

    root = tk.Tk()
    root.title("Animal Escape — Statistics")
    root.configure(bg="#1e1e2e")
    root.geometry("1100x820")
    root.resizable(True, True)

    # ---- Header ----
    header = tk.Label(root, text="📊  Game Statistics",
                      font=("Verdana", 18, "bold"),
                      bg="#1e1e2e", fg="#cdd6f4")
    header.pack(pady=(12, 0))

    total_rows = len(rows)
    sub = tk.Label(root, text=f"Total records: {total_rows}   |   CSV: {CSV_FILE}",
                   font=("Verdana", 9), bg="#1e1e2e", fg="#a6adc8")
    sub.pack(pady=(0, 8))

    # ---- Notebook (tabs) ----
    style = ttk.Style()
    style.theme_use("default")
    style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
    style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4",
                    padding=[12, 5], font=("Verdana", 9, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", "#89b4fa")],
              foreground=[("selected", "#1e1e2e")])

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=10, pady=4)

    # ---- Tab 1: กราฟทั้งหมด ----
    tab_graphs = tk.Frame(nb, bg="#1e1e2e")
    nb.add(tab_graphs, text="  📈 All Graphs  ")

    fig = plt.Figure(figsize=(14, 9), facecolor="#1e1e2e")
    fig.subplots_adjust(hspace=0.45, wspace=0.35,
                        left=0.07, right=0.97, top=0.95, bottom=0.07)

    gs = gridspec.GridSpec(2, 3, figure=fig)
    ax1 = fig.add_subplot(gs[0, 0])   # Pie
    ax2 = fig.add_subplot(gs[0, 1])   # Zone Bar
    ax3 = fig.add_subplot(gs[0, 2])   # Mana Line
    ax4 = fig.add_subplot(gs[1, 0:2]) # HP Area (wide)
    ax5 = fig.add_subplot(gs[1, 2])   # Proximity Bar

    for ax in [ax1, ax2, ax3, ax4, ax5]:
        ax.set_facecolor("#313244")
        ax.tick_params(colors="#cdd6f4", labelsize=8)
        ax.title.set_color("#cdd6f4")
        for spine in ax.spines.values():
            spine.set_edgecolor("#585b70")
        if hasattr(ax, 'xaxis'):
            ax.xaxis.label.set_color("#a6adc8")
            ax.yaxis.label.set_color("#a6adc8")

    build_pie_chart(ax1, rows)
    build_zone_bar(ax2, rows)
    build_mana_line(ax3, rows)
    build_hp_area(ax4, rows)
    build_enemy_proximity_bar(ax5, rows)

    canvas = FigureCanvasTkAgg(fig, master=tab_graphs)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---- Tab 2: Summary Stats Table ----
    tab_table = tk.Frame(nb, bg="#1e1e2e")
    nb.add(tab_table, text="  📋 Summary Stats  ")

    tk.Label(tab_table, text="Statistical Summary",
             font=("Verdana", 14, "bold"), bg="#1e1e2e", fg="#cdd6f4").pack(pady=12)

    cols = ("Feature", "Mean", "Median", "Max", "Min")
    tree = ttk.Treeview(tab_table, columns=cols, show="headings", height=8)
    style.configure("Treeview", background="#313244", foreground="#cdd6f4",
                    fieldbackground="#313244", font=("Verdana", 10),
                    rowheight=32)
    style.configure("Treeview.Heading", background="#89b4fa", foreground="#1e1e2e",
                    font=("Verdana", 10, "bold"))
    style.map("Treeview", background=[("selected", "#585b70")])

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=180, anchor="center")

    summary = build_summary(rows)
    for i, row in enumerate(summary):
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=row, tags=(tag,))
    tree.tag_configure("even", background="#313244")
    tree.tag_configure("odd",  background="#2a2a3d")

    tree.pack(padx=30, pady=10, fill="x")

    # จำนวน sessions
    sessions = len([r for r in rows if r["event"] == "game_over"])
    chars_played = defaultdict(int)
    for r in rows:
        if r["event"] == "game_over":
            chars_played[r["char_type"]] += 1

    info_frame = tk.Frame(tab_table, bg="#1e1e2e")
    info_frame.pack(pady=20)

    tk.Label(info_frame, text=f"Total Sessions Played: {sessions}",
             font=("Verdana", 11), bg="#1e1e2e", fg="#a6e3a1").grid(row=0, column=0, padx=30)

    char_text = "   ".join([f"{k}: {v}x" for k, v in chars_played.items()]) or "—"
    tk.Label(info_frame, text=f"Characters Used:  {char_text}",
             font=("Verdana", 11), bg="#1e1e2e", fg="#89dceb").grid(row=0, column=1, padx=30)

    total_items = len([r for r in rows if r["event"] == "item_collect"])
    tk.Label(info_frame, text=f"Total Items Collected: {total_items}",
             font=("Verdana", 11), bg="#1e1e2e", fg="#f9e2af").grid(row=0, column=2, padx=30)

    # ---- Tab 3: Raw Data ----
    tab_raw = tk.Frame(nb, bg="#1e1e2e")
    nb.add(tab_raw, text="  🗃️ Raw Data  ")

    tk.Label(tab_raw, text="Recent Records (latest 200)",
             font=("Verdana", 11, "bold"), bg="#1e1e2e", fg="#cdd6f4").pack(pady=8)

    raw_cols = ["timestamp","event","char_type","score","hp","mana",
                "player_x","player_y","enemy_dist","item_type","survival_time"]
    raw_tree = ttk.Treeview(tab_raw, columns=raw_cols, show="headings", height=22)
    for col in raw_cols:
        raw_tree.heading(col, text=col)
        raw_tree.column(col, width=90, anchor="center")

    scrollbar = ttk.Scrollbar(tab_raw, orient="vertical", command=raw_tree.yview)
    raw_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    raw_tree.pack(fill="both", expand=True, padx=10)

    display_rows = rows[-200:]  # แสดง 200 แถวล่าสุด
    for i, r in enumerate(reversed(display_rows)):
        vals = [r.get(c, "") for c in raw_cols]
        tag = "even" if i % 2 == 0 else "odd"
        raw_tree.insert("", "end", values=vals, tags=(tag,))
    raw_tree.tag_configure("even", background="#313244")
    raw_tree.tag_configure("odd",  background="#2a2a3d")

    # ---- Bottom bar ----
    bottom = tk.Frame(root, bg="#181825")
    bottom.pack(fill="x", side="bottom")

    def refresh():
        root.destroy()
        open_stats_window()

    tk.Button(bottom, text="🔄 Refresh", command=refresh,
              bg="#89b4fa", fg="#1e1e2e", font=("Verdana", 9, "bold"),
              relief="flat", padx=12, pady=4).pack(side="left", padx=10, pady=6)

    def clear_data():
        if messagebox.askyesno("Clear Data", "ลบข้อมูลสถิติทั้งหมด?"):
            open(CSV_FILE, "w", newline="", encoding="utf-8").close()
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                import csv as _csv
                w = _csv.DictWriter(f, fieldnames=[
                    "timestamp","event","char_type","score","hp","mana",
                    "player_x","player_y","enemy_x","enemy_y","enemy_dist",
                    "item_type","survival_time"
                ])
                w.writeheader()
            root.destroy()
            open_stats_window()

    tk.Button(bottom, text="🗑️ Clear Data", command=clear_data,
              bg="#f38ba8", fg="#1e1e2e", font=("Verdana", 9, "bold"),
              relief="flat", padx=12, pady=4).pack(side="left", padx=4, pady=6)

    tk.Label(bottom, text="Animal Escape Stats Viewer  |  data: stats.csv",
             bg="#181825", fg="#585b70", font=("Verdana", 8)).pack(side="right", padx=12)

    root.mainloop()


if __name__ == "__main__":
    open_stats_window()