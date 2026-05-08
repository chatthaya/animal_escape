import pygame
import sys
import subprocess

try:
    from map_manager import Game, GAME_WIDTH, GAME_HEIGHT, preload_game_assets
except ImportError:
    Game = None
    GAME_WIDTH, GAME_HEIGHT = 900, 800
    def preload_game_assets(): return {}

pygame.init()
SW, SH = 900, 800
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Animal Escape - Maze Survival")

def load_bg_image(name, w, h):
    try:
        from PIL import Image
        pil = Image.open(name).convert("RGB")
        pil = pil.resize((w, h), Image.LANCZOS)
        return pygame.image.frombuffer(pil.tobytes(), (w, h), "RGB").convert()
    except Exception:
        try:
            return pygame.transform.smoothscale(pygame.image.load(name).convert(), (w, h))
        except Exception:
            s = pygame.Surface((w, h)); s.fill((10, 60, 140)); return s

loading_bg = load_bg_image("load.jpg", SW, SH)

def draw_loading_screen(progress, label_text="Loading..."):
    screen.blit(loading_bg, (0, 0))
    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 90))
    screen.blit(overlay, (0, 0))

    _font_title = pygame.font.SysFont("Arial", 60, bold=True)
    _title_sh = _font_title.render("Animal Escape", True, (60, 30, 0))
    _title    = _font_title.render("Animal Escape", True, (255, 230, 80))
    tx = SW//2 - _title.get_width()//2
    screen.blit(_title_sh, (tx + 3, SH//2 - 130 + 3))
    screen.blit(_title,    (tx,     SH//2 - 130))

    _font_lbl = pygame.font.SysFont("Arial", 30, bold=True)
    _lbl    = _font_lbl.render(label_text, True, (240, 255, 220))
    _lbl_sh = _font_lbl.render(label_text, True, (0, 0, 0))
    lx = SW//2 - _lbl.get_width()//2
    screen.blit(_lbl_sh, (lx + 2, SH//2 - 14))
    screen.blit(_lbl,    (lx,     SH//2 - 16))

    BAR_W, BAR_H = 560, 40
    bx = SW//2 - BAR_W//2
    by = SH//2 + 36

    pygame.draw.rect(screen, (0, 0, 0, 120), (bx + 4, by + 4, BAR_W, BAR_H), border_radius=20)
    pygame.draw.rect(screen, (30, 20, 10), (bx, by, BAR_W, BAR_H), border_radius=20)

    fill_w = max(0, int((BAR_W - 8) * progress))
    if fill_w > 0:
        fill_rect = pygame.Rect(bx + 4, by + 4, fill_w, BAR_H - 8)
        pygame.draw.rect(screen, (180, 210, 40), fill_rect, border_radius=16)
        hi_rect = pygame.Rect(bx + 4, by + 4, fill_w, (BAR_H - 8)//3)
        pygame.draw.rect(screen, (220, 255, 80), hi_rect, border_radius=16)
        if fill_w > 20:
            shimmer_surf = pygame.Surface((18, BAR_H - 8), pygame.SRCALPHA)
            shimmer_surf.fill((255, 255, 255, 50))
            screen.blit(shimmer_surf, (bx + 4 + fill_w - 22, by + 4))

    pygame.draw.rect(screen, (180, 130, 40), (bx, by, BAR_W, BAR_H), 4, border_radius=20)
    pygame.draw.rect(screen, (120, 80, 20),  (bx + 2, by + 2, BAR_W - 4, BAR_H - 4), 2, border_radius=18)

    _font_pct = pygame.font.SysFont("Arial", 20, bold=True)
    _pct    = _font_pct.render(f"{int(progress * 100)}%", True, (230, 255, 180))
    _pct_sh = _font_pct.render(f"{int(progress * 100)}%", True, (0, 0, 0))
    px = SW//2 - _pct.get_width()//2
    screen.blit(_pct_sh, (px + 1, by + BAR_H + 9))
    screen.blit(_pct,    (px,     by + BAR_H + 8))

    pygame.display.flip()
    pygame.event.pump()


draw_loading_screen(0.0)

characters = [
    {"name": "Pig",    "hp": 250, "mp": 50,  "img_file": "play_pig.png",   "bonus": ""},
    {"name": "Rabbit", "hp": 200, "mp": 75,  "img_file": "play_rab.png",   "bonus": ""},
    {"name": "Sheep",  "hp": 100, "mp": 25,  "img_file": "play_sheep.png", "bonus": "Bonus : x2 Item Points"},
]

def load_bg(name):
    try:
        from PIL import Image
        pil = Image.open(name).convert("RGB")
        pil = pil.resize((SW, SH), Image.LANCZOS)
        return pygame.image.frombuffer(pil.tobytes(), (SW, SH), "RGB").convert()
    except Exception:
        try:
            return pygame.transform.smoothscale(pygame.image.load(name).convert(), (SW, SH))
        except Exception:
            s = pygame.Surface((SW, SH)); s.fill((50, 70, 50)); return s

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

draw_loading_screen(0.95, "Loading game assets...")
game_assets = preload_game_assets()
draw_loading_screen(1.0, "Ready!")
pygame.time.wait(600)

import math
_font_candidates = ["Fredoka One", "Baloo 2", "Nunito", "Varela Round",
                    "Arial Rounded MT Bold", "Comic Sans MS", "Arial"]

# ปุ่มใหญ่ (PLAY, STATISTICS, BACK, START) — ไม่ bold เพื่อตัวบางลง
font_btn = None
for _fc in _font_candidates:
    try:
        _f = pygame.font.SysFont(_fc, 42, bold=False)
        font_btn = _f
        break
    except Exception:
        pass
if font_btn is None:
    font_btn = pygame.font.SysFont("Arial", 42, bold=False)

# ปุ่มเล็ก (EXIT) — ขนาดเล็กกว่า
font_btn_small = None
for _fc in _font_candidates:
    try:
        _f = pygame.font.SysFont(_fc, 30, bold=False)
        font_btn_small = _f
        break
    except Exception:
        pass
if font_btn_small is None:
    font_btn_small = pygame.font.SysFont("Arial", 30, bold=False)


def _render_outlined(font, text, color, outline_color, thickness=3, spacing=2):
    """วาด text พร้อม outline + letter spacing"""
    # วาดทีละตัว แทรก spacing
    chars = list(text)
    char_surfs = [font.render(c, True, color) for c in chars]
    char_outs  = [font.render(c, True, outline_color) for c in chars]
    pad = thickness
    total_w = sum(s.get_width() for s in char_surfs) + spacing * max(0, len(chars)-1) + pad*2
    total_h = max((s.get_height() for s in char_surfs), default=0) + pad*2
    surf = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
    x = pad
    for base, out in zip(char_surfs, char_outs):
        for dx in range(-thickness, thickness+1):
            for dy in range(-thickness, thickness+1):
                if dx == 0 and dy == 0: continue
                if abs(dx) + abs(dy) <= thickness + 1:
                    surf.blit(out, (x + dx, pad + dy))
        surf.blit(base, (x, pad))
        x += base.get_width() + spacing
    return surf

BTN_W, BTN_H = 380, 80
BTN_PLAY  = pygame.Rect(SW//2 - BTN_W//2, SH//2 - 20,  BTN_W, BTN_H)
BTN_STATS = pygame.Rect(SW//2 - BTN_W//2, SH//2 + 82,  BTN_W, BTN_H)

# ปุ่ม EXIT มุมล่างซ้าย — ใช้ทั้งสองหน้า
BTN_EXIT = pygame.Rect(30, SH - 74, 160, 52)

CARD_RECTS = [
    pygame.Rect(65,  195, 760, 135),
    pygame.Rect(65,  368, 760, 135),
    pygame.Rect(65,  522, 760, 140),
]

CIRCLE_CENTERS = [(145, 265), (145, 435), (145, 592)]
CIRCLE_R = 68

BTN_BACK  = pygame.Rect(60,  710, 160, 60)
BTN_START = pygame.Rect(680, 710, 160, 60)


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


def draw_wood_btn(surface, rect, text, style="brown", hover=False, greyed=False, font=None):
    if font is None:
        font = font_btn
    if greyed:
        fill_base = (90, 90, 90)
        border_c  = (55, 55, 55)
        hi_c      = (120, 120, 120)
        txt_col   = (180, 180, 180)
        out_col   = (40, 40, 40)
    elif style == "green":
        fill_base = (60, 200, 50) if not hover else (80, 225, 65)
        border_c  = (20, 110, 15)
        hi_c      = (160, 255, 120)
        txt_col   = (255, 255, 255)
        out_col   = (20, 90, 10)
    elif style == "gold":
        fill_base = (255, 195, 30) if not hover else (255, 215, 55)
        border_c  = (150, 90, 10)
        hi_c      = (255, 240, 130)
        txt_col   = (255, 255, 255)
        out_col   = (120, 65, 5)
    elif style == "red":
        fill_base = (220, 50, 30) if not hover else (245, 70, 45)
        border_c  = (120, 20, 10)
        hi_c      = (255, 120, 100)
        txt_col   = (255, 255, 255)
        out_col   = (100, 15, 5)
    else:
        fill_base = (195, 130, 50) if not hover else (215, 150, 65)
        border_c  = (110, 70, 20)
        hi_c      = (230, 180, 110)
        txt_col   = (255, 245, 200)
        out_col   = (80, 45, 10)

    pygame.draw.rect(surface, (15, 10, 5), rect.move(5, 5), border_radius=20)
    pygame.draw.rect(surface, fill_base, rect, border_radius=20)
    pygame.draw.rect(surface, border_c, rect, 5, border_radius=20)
    hi = pygame.Rect(rect.x + 16, rect.y + 8, rect.width - 32, 8)
    pygame.draw.rect(surface, hi_c, hi, border_radius=6)

    lbl_surf = _render_outlined(font, text, txt_col, out_col, thickness=3, spacing=2)
    bx = rect.centerx - lbl_surf.get_width()  // 2
    by = rect.centery - lbl_surf.get_height() // 2
    surface.blit(lbl_surf, (bx, by))


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

            # ปุ่ม EXIT ใช้ได้เฉพาะหน้า OPEN เท่านั้น
            if state == "OPEN" and BTN_EXIT.collidepoint((mx, my)):
                pygame.quit(); sys.exit()

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
                        screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                        game_engine = Game(characters[selected_idx], screen, game_assets)
                        result = game_engine.run()
                        screen = pygame.display.set_mode((SW, SH))
                        if result == "SELECT":
                            state = "SELECT"; selected_idx = None
                        else:
                            state = "OPEN"; selected_idx = None
                    else:
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

        draw_wood_btn(screen, BTN_EXIT, "EXIT",
                      style="red",
                      hover=BTN_EXIT.collidepoint((mx, my)),
                      font=font_btn_small)

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