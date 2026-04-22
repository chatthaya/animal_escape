import pygame
import sys
import subprocess

# --- import map_manager แบบ safe ---
try:
    from map_manager import Game
except ImportError:
    Game = None

pygame.init()
SW, SH = 900, 800
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Animal Escape - Maze Survival")

# ===== ฟังก์ชัน Loading Screen พร้อม Progress Bar =====
def draw_loading_screen(progress, label_text="Loading..."):
    """วาด loading screen พื้นฟ้า + หลอด gold กรอบเขียว"""
    # พื้นหลังไล่สีฟ้า
    for y in range(SH):
        t = y / SH
        r = int(10  + (30  - 10)  * t)
        g = int(60  + (100 - 60)  * t)
        b = int(140 + (200 - 140) * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (SW, y))

    # ชื่อเกม
    _font_title = pygame.font.SysFont("Arial", 52, bold=True)
    _title_sh = _font_title.render("Animal Escape", True, (80, 50, 0))
    _title    = _font_title.render("Animal Escape", True, (255, 230, 80))
    tx = SW//2 - _title.get_width()//2
    screen.blit(_title_sh, (tx + 3, SH//2 - 120 + 3))
    screen.blit(_title,    (tx,     SH//2 - 120))

    # ข้อความ Loading
    _font_lbl = pygame.font.SysFont("Arial", 32, bold=True)
    _lbl = _font_lbl.render(label_text, True, (200, 230, 255))
    screen.blit(_lbl, (SW//2 - _lbl.get_width()//2, SH//2 - 18))

    # หลอด progress bar
    BAR_W, BAR_H = 560, 44
    bx = SW//2 - BAR_W//2
    by = SH//2 + 40

    # เงาหลอด
    pygame.draw.rect(screen, (10, 20, 50), (bx + 4, by + 4, BAR_W, BAR_H), border_radius=22)
    # พื้นหลังหลอด (สีเข้ม)
    pygame.draw.rect(screen, (15, 30, 70), (bx, by, BAR_W, BAR_H), border_radius=22)

    # ส่วนที่โหลดแล้ว (gold)
    fill_w = max(0, int((BAR_W - 8) * progress))
    if fill_w > 0:
        fill_rect = pygame.Rect(bx + 4, by + 4, fill_w, BAR_H - 8)
        pygame.draw.rect(screen, (200, 155, 20), fill_rect, border_radius=18)
        # ไฮไลต์สีทองสว่างด้านบน
        hi_rect = pygame.Rect(bx + 4, by + 4, fill_w, (BAR_H - 8)//3)
        pygame.draw.rect(screen, (255, 215, 80), hi_rect, border_radius=18)
        # shimmer
        if fill_w > 20:
            shimmer_surf = pygame.Surface((18, BAR_H - 8), pygame.SRCALPHA)
            shimmer_surf.fill((255, 255, 255, 55))
            screen.blit(shimmer_surf, (bx + 4 + fill_w - 22, by + 4))

    # กรอบสีเขียว
    pygame.draw.rect(screen, (40, 200, 80), (bx, by, BAR_W, BAR_H), 4, border_radius=22)
    pygame.draw.rect(screen, (20, 120, 50), (bx + 2, by + 2, BAR_W - 4, BAR_H - 4), 2, border_radius=20)

    # เปอร์เซ็นต์
    _font_pct = pygame.font.SysFont("Arial", 22, bold=True)
    _pct = _font_pct.render(f"{int(progress * 100)}%", True, (220, 255, 220))
    screen.blit(_pct, (SW//2 - _pct.get_width()//2, by + BAR_H + 10))

    pygame.display.flip()
    pygame.event.pump()


# ===== แสดง Loading Screen เริ่มต้น =====
draw_loading_screen(0.0)
# ==========================================

characters = [
    {"name": "Pig",    "hp": 250, "mp": 50,  "img_file": "play_pig.png",   "bonus": ""},
    {"name": "Rabbit", "hp": 200, "mp": 75,  "img_file": "play_rab.png",   "bonus": ""},
    {"name": "Sheep",  "hp": 100, "mp": 25,  "img_file": "play_sheep.png", "bonus": "Bonus : x2 Item Points"},
]

def load_bg(name):
    """โหลดด้วย PIL Lanczos — fallback smoothscale — fallback solid color"""
    try:
        from PIL import Image
        pil = Image.open(name).convert("RGB")
        pil = pil.resize((SW, SH), Image.LANCZOS)
        return pygame.image.frombuffer(pil.tobytes(), (SW, SH), "RGB").convert()
    except Exception:
        try:
            return pygame.transform.smoothscale(
                pygame.image.load(name).convert(), (SW, SH))
        except Exception:
            s = pygame.Surface((SW, SH)); s.fill((50, 70, 50)); return s

# โหลดภาพทั้งหมด พร้อมอัปเดต progress bar ทีละไฟล์
_assets = [
    ("main.png",   "Loading main menu..."),
    ("select.png", "Loading select screen..."),
    ("pig.png",    "Loading Pig..."),
    ("rabbit.png", "Loading Rabbit..."),
    ("sheep.png",  "Loading Sheep..."),
]
_loaded_bgs = []
for _i, (_fname, _label) in enumerate(_assets):
    draw_loading_screen(_i / len(_assets), _label)
    _loaded_bgs.append(load_bg(_fname))
    draw_loading_screen((_i + 1) / len(_assets), _label)

bg_main, bg_select, bg_pig, bg_rabbit, bg_sheep = _loaded_bgs
BG_CHARS = [bg_pig, bg_rabbit, bg_sheep]

# หลอดเต็ม 100% — หยุดสักครู่แล้วเข้าเกม
draw_loading_screen(1.0, "Ready!")
pygame.time.wait(600)

# ---- ฟอนต์ปุ่ม ----
import math
_font_candidates = ["Baloo 2", "Fredoka One", "Nunito", "Varela Round",
                    "Comic Sans MS", "Arial Rounded MT Bold", "Arial"]
font_btn = None
for _fc in _font_candidates:
    try:
        _f = pygame.font.SysFont(_fc, 40, bold=True)
        font_btn = _f
        break
    except Exception:
        pass
if font_btn is None:
    font_btn = pygame.font.SysFont("Arial", 40, bold=True)

# ---- ปุ่ม PLAY / STATISTICS ในหน้าหลัก ----
# ใหญ่ขึ้น + เลื่อนลงมาตรงกลางแนวตั้งมากขึ้น
BTN_W, BTN_H = 380, 80
BTN_PLAY  = pygame.Rect(SW//2 - BTN_W//2, SH//2 - 20,  BTN_W, BTN_H)
BTN_STATS = pygame.Rect(SW//2 - BTN_W//2, SH//2 + 82,  BTN_W, BTN_H)

# ---- hitbox การ์ดตัวละครในหน้า select ----
CARD_RECTS = [
    pygame.Rect(65,  195, 760, 135),   # Pig
    pygame.Rect(65,  368, 760, 135),   # Rabbit
    pygame.Rect(65,  522, 760, 140),   # Sheep
]

CIRCLE_CENTERS = [(145, 265), (145, 435), (145, 592)]
CIRCLE_R = 68

# ปุ่ม BACK / START ในหน้า select
BTN_BACK  = pygame.Rect(60,  718, 160, 52)
BTN_START = pygame.Rect(680, 718, 160, 52)


def draw_checkmark(surface, cx, cy, r=18):
    pygame.draw.circle(surface, (20, 175, 20), (cx, cy), r)
    pygame.draw.circle(surface, (10, 110, 10), (cx, cy), r, 3)
    pygame.draw.circle(surface, (200, 255, 200), (cx - r//5, cy - r//4), r//4)
    pts = [
        (cx - r//2 + 2,  cy + 1),
        (cx - 2,          cy + r//2 - 1),
        (cx + r//2 + 2,  cy - r//3),
    ]
    pygame.draw.lines(surface, (255, 255, 255), False, pts, 3)


def draw_wood_btn(surface, rect, text, style="brown", hover=False, greyed=False):
    if greyed:
        fill_base = (90, 90, 90)
        border_c  = (55, 55, 55)
        hi_c      = (120, 120, 120)
        txt_col   = (160, 160, 160)
    elif style == "green":
        fill_base = (105, 185, 55) if not hover else (125, 205, 70)
        border_c  = (145, 100, 30)
        hi_c      = (165, 235, 110)
        txt_col   = (255, 255, 255)
    elif style == "gold":
        fill_base = (215, 170, 40) if not hover else (235, 190, 55)
        border_c  = (145, 100, 30)
        hi_c      = (255, 225, 100)
        txt_col   = (255, 255, 255)
    else:  # brown
        fill_base = (175, 120, 45) if not hover else (195, 140, 60)
        border_c  = (110, 70, 20)
        hi_c      = (220, 165, 90)
        txt_col   = (255, 245, 200)

    # เงา
    pygame.draw.rect(surface, (15, 10, 5), rect.move(5, 5), border_radius=20)
    # ตัวปุ่ม
    pygame.draw.rect(surface, fill_base, rect, border_radius=20)
    # กรอบไม้
    pygame.draw.rect(surface, border_c, rect, 5, border_radius=20)
    # ไฮไลต์บน
    hi = pygame.Rect(rect.x + 16, rect.y + 8, rect.width - 32, 8)
    pygame.draw.rect(surface, hi_c, hi, border_radius=6)
    # ข้อความ + เงา
    lbl = font_btn.render(text, True, txt_col)
    sh  = font_btn.render(text, True, (30, 15, 0) if not greyed else (40, 40, 40))
    bx  = rect.centerx - lbl.get_width()  // 2
    by  = rect.centery - lbl.get_height() // 2
    surface.blit(sh,  (bx + 2, by + 2))
    surface.blit(lbl, (bx, by))


def open_statistics():
    try:
        subprocess.Popen([sys.executable, "stats_viewer.py"])
    except Exception as e:
        print(f"[Stats] {e}")


state        = "OPEN"
selected_idx = None
clock        = pygame.time.Clock()

while True:
    mx, my = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:

            if state == "OPEN":
                if BTN_PLAY.collidepoint((mx, my)):
                    state = "SELECT"; selected_idx = None
                elif BTN_STATS.collidepoint((mx, my)):
                    open_statistics()

            elif state == "SELECT":
                for i, rect in enumerate(CARD_RECTS):
                    if rect.collidepoint((mx, my)):
                        selected_idx = i

                if BTN_BACK.collidepoint((mx, my)):
                    state = "OPEN"; selected_idx = None

                if selected_idx is not None and BTN_START.collidepoint((mx, my)):
                    if Game is not None:
                        game_engine = Game(characters[selected_idx])
                        game_engine.run()
                    state = "OPEN"; selected_idx = None

    # -------- วาด --------
    if state == "OPEN":
        screen.blit(bg_main, (0, 0))

        draw_wood_btn(screen, BTN_PLAY, "PLAY",
                      style="green",
                      hover=BTN_PLAY.collidepoint((mx, my)))

        draw_wood_btn(screen, BTN_STATS, "STATISTICS",
                      style="gold",
                      hover=BTN_STATS.collidepoint((mx, my)))

    elif state == "SELECT":
        if selected_idx is not None:
            screen.blit(BG_CHARS[selected_idx], (0, 0))
        else:
            screen.blit(bg_select, (0, 0))

        draw_wood_btn(screen, BTN_BACK, "BACK",
                      style="gold",
                      hover=BTN_BACK.collidepoint((mx, my)))

        can_start = selected_idx is not None
        draw_wood_btn(screen, BTN_START, "START!",
                      style="green",
                      hover=(can_start and BTN_START.collidepoint((mx, my))),
                      greyed=not can_start)

    pygame.display.flip()
    clock.tick(60)