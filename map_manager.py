import pygame
import random
import math
import sys
from player import Player
from enemy import Wolf
from item import Item, HealItem, ShieldItem, ClockItem, WallItem, StarItem, TrapItem, WaterTrap, PlacedTrap
from stats_logger import StatsLogger

TILE_SIZE = 30
GRID_SIZE_X = 26
GRID_SIZE_Y = 20
MARGIN = 40
UI_HEIGHT = 140
GAME_WIDTH = (TILE_SIZE * GRID_SIZE_X) + (MARGIN * 2)
GAME_HEIGHT = (TILE_SIZE * GRID_SIZE_Y) + UI_HEIGHT + MARGIN

COLOR_BG_MAIN = (255, 255, 224)
COLOR_GRASS = (145, 189, 89)
COLOR_GRASS_LIGHT = (160, 205, 100)
COLOR_WALL = (195, 195, 195)
COLOR_WALL_DARK = (130, 130, 130)
COLOR_WALL_LIGHT = (230, 230, 230)
COLOR_BORDER = (210, 160, 120)
COLOR_BORDER_DARK = (160, 110, 70)
COLOR_HP = (220, 20, 60)
COLOR_MP = (30, 144, 255)
COLOR_TEXT_DARK = (50, 50, 50)
COLOR_BAR_BG = (180, 180, 180)
COLOR_TEXT_HP = (0, 0, 0)
COLOR_SCORE_TEXT = (255, 255, 255)
COLOR_SCORE_OUTLINE = (101, 67, 33)

# ธีมสีไม้ — ใช้ซ้ำทั้งไฟล์
WOOD_DARK   = (101,  67,  33)
WOOD_MID    = (160, 110,  60)
WOOD_LIGHT  = (210, 165, 100)
WOOD_HI     = (235, 200, 145)
PARCHMENT   = (245, 225, 175)


def preload_game_assets():
    assets = {}
    try:
        bg = pygame.image.load("bg.jpg").convert()
        assets["bg_image"] = pygame.transform.scale(bg, (GAME_WIDTH, GAME_HEIGHT))
    except:
        assets["bg_image"] = None
        print("Warning: bg.jpg not found, using default background color.")

    # โหลด pause.png สำหรับ pause overlay panel
    try:
        raw = pygame.image.load("pause.png").convert_alpha()
        assets["pause_panel"] = raw
    except:
        assets["pause_panel"] = None

    # โหลด gameover.png สำหรับ game over panel
    try:
        raw = pygame.image.load("gameover.png").convert_alpha()
        assets["gameover_panel"] = raw
    except:
        assets["gameover_panel"] = None

    # โหลด character portrait images (play_pig, play_rab, play_sheep)
    char_files = {
        "Pig":    "play_pig.png",
        "Rabbit": "play_rab.png",
        "Sheep":  "play_sheep.png",
    }
    portraits = {}
    for name, fname in char_files.items():
        try:
            raw = pygame.image.load(fname).convert_alpha()
            portraits[name] = raw
        except:
            portraits[name] = None
    assets["portraits"] = portraits

    return assets


# ===== helper: วาด text พร้อม outline + letter spacing =====
def _render_outlined(font, text, color, outline_color, thickness=3, spacing=2):
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


# ===== วาดปุ่มสไตล์ไม้ (ใช้ใน pause menu) =====
def _draw_wood_btn_game(surface, rect, text, font, style="green", hover=False, font_small=None):
    if style == "green":
        fill  = (60, 200, 50) if not hover else (80, 225, 65)
        bord  = (20, 110, 15)
        hi_c  = (160, 255, 120)
        tc    = (255, 255, 255)
        oc    = (20, 90, 10)
    elif style == "red":
        fill  = (220, 50, 30) if not hover else (245, 70, 45)
        bord  = (120, 20, 10)
        hi_c  = (255, 120, 100)
        tc    = (255, 255, 255)
        oc    = (100, 15, 5)
    else:  # gold
        fill  = (255, 195, 30) if not hover else (255, 215, 55)
        bord  = (150, 90, 10)
        hi_c  = (255, 240, 130)
        tc    = (255, 255, 255)
        oc    = (120, 65, 5)

    pygame.draw.rect(surface, fill, rect, border_radius=18)
    pygame.draw.rect(surface, bord, rect, 4, border_radius=18)
    hi = pygame.Rect(rect.x + 14, rect.y + 7, rect.width - 28, 7)
    pygame.draw.rect(surface, hi_c, hi, border_radius=5)

    # ถ้า text ยาวและมี font_small ให้ใช้ font_small แทน
    use_font = font_small if (font_small and font_small.size(text)[0] + 20 > rect.width) else font
    lbl_surf = _render_outlined(use_font, text, tc, oc, thickness=3, spacing=2)
    bx = rect.centerx - lbl_surf.get_width()  // 2
    by = rect.centery - lbl_surf.get_height() // 2
    surface.blit(lbl_surf, (bx, by))


class Game:
    def __init__(self, char_data, screen, assets):
        self.screen = screen
        self.bg_image      = assets.get("bg_image")
        self.pause_panel   = assets.get("pause_panel")
        self.gameover_panel = assets.get("gameover_panel")
        self.portraits     = assets.get("portraits", {})

        self.clock    = pygame.time.Clock()
        self.font     = pygame.font.SysFont("Verdana", 24, bold=True)
        self.bar_font = pygame.font.SysFont("Verdana", 16, bold=True)

        # ฟ้อนสำหรับ pause menu — cartoon rounded bold
        _candidates = ["Fredoka One", "Baloo 2", "Nunito", "Varela Round",
                       "Arial Rounded MT Bold", "Comic Sans MS", "Arial"]
        self.pause_font = None
        for fc in _candidates:
            try:
                self.pause_font = pygame.font.SysFont(fc, 24, bold=False)
                break
            except:
                pass
        if self.pause_font is None:
            self.pause_font = pygame.font.SysFont("Arial", 24, bold=False)

        # ฟ้อนเล็กสำหรับปุ่มที่ข้อความยาว (RETURN TO MENU)
        self.pause_font_small = None
        for fc in _candidates:
            try:
                self.pause_font_small = pygame.font.SysFont(fc, 22, bold=False)
                break
            except:
                pass
        if self.pause_font_small is None:
            self.pause_font_small = pygame.font.SysFont("Arial", 22, bold=False)

        self.flash_alpha = 0
        self.flash_dir   = 1
        self.all_occupied_positions = set()
        self.paused = False

        # สร้าง portrait circle สำหรับวาดใน UI
        self._char_name = char_data["name"]
        self._build_avatar(char_data)

        self.grid_data = [
            [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],
            [2,0,0,1,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1,0,0,2],
            [2,0,0,0,0,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,0,2],
            [2,0,1,1,0,1,1,0,0,1,0,0,0,1,0,0,0,0,1,0,1,0,1,1,0,2],
            [2,0,0,1,0,0,0,0,0,0,0,1,0,0,0,1,1,0,0,0,1,0,0,0,0,2],
            [2,0,0,0,0,1,1,0,1,0,0,1,0,0,1,1,0,0,0,0,0,0,1,1,1,2],
            [2,1,1,0,0,0,1,0,0,1,0,1,1,0,0,0,0,1,1,0,1,0,0,0,0,2],
            [2,1,0,0,1,0,0,0,0,1,0,0,0,0,1,1,0,0,1,0,1,1,0,1,0,2],
            [2,0,0,0,1,1,1,0,0,0,0,1,0,0,0,1,1,0,0,0,0,1,0,1,1,2],
            [2,0,1,0,0,0,1,0,1,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,2],
            [2,0,1,0,1,0,0,0,1,0,0,0,0,0,0,1,0,1,0,0,0,0,1,1,0,2],
            [2,0,0,0,0,0,1,0,1,0,1,0,0,1,0,0,0,0,0,1,1,1,0,0,0,2],
            [2,1,1,1,0,1,1,0,0,0,1,1,0,1,0,1,0,1,0,0,0,0,0,1,0,2],
            [2,0,0,0,0,0,0,0,1,0,0,1,0,0,0,1,0,1,1,0,0,1,0,1,0,2],
            [2,0,1,0,1,1,0,1,1,1,0,0,0,1,0,1,0,0,0,0,1,1,0,0,0,2],
            [2,0,1,0,0,0,0,1,0,0,0,0,1,1,0,0,0,1,0,0,0,1,0,1,1,2],
            [2,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,1,0,1,0,0,0,0,1,2],
            [2,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,0,0,0,1,1,0,1,0,0,2],
            [2,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,0,0,2],
            [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],
        ]

        self.player = Player(char_data)
        self.wolf   = Wolf()
        self.game_over   = False
        self.active_traps = []
        self.water_traps  = []
        self.stats = StatsLogger(char_data["name"])

        self.water_relocate_timer      = 0
        self.last_water_score_threshold = 0
        self.BASE_WATER_COUNT = 3
        self.spawn_items_no_overlap()
        self._spawn_water_traps(self.BASE_WATER_COUNT)

        # ===== Pause button — เล็ก ชิดขวาบน =====
        self.PAUSE_BTN_R  = 22
        self.PAUSE_BTN_CX = GAME_WIDTH - 38
        self.PAUSE_BTN_CY = 38

        # ===== Pause menu rects — ใหญ่ขึ้น ปุ่มไม่เกินกรอบ =====
        PW, PH = 500, 580
        self.pause_menu_rect = pygame.Rect(
            GAME_WIDTH  // 2 - PW // 2,
            GAME_HEIGHT // 2 - PH // 2,
            PW, PH
        )
        btn_w, btn_h = 170, 42
        cx = GAME_WIDTH // 2
        exit_y   = self.pause_menu_rect.y + 376   # EXIT คงตำแหน่งเดิม
        resume_y = self.pause_menu_rect.y + 210   # RESUME ขอบบนตรงขีดเขียว
        menu_y   = (resume_y + exit_y) // 2       # MENU กึ่งกลางระหว่างสองปุ่ม
        self.PBTN_RESUME = pygame.Rect(cx - btn_w//2, resume_y, btn_w, btn_h)
        self.PBTN_MENU   = pygame.Rect(cx - btn_w//2, menu_y,   btn_w, btn_h)
        self.PBTN_EXIT   = pygame.Rect(cx - btn_w//2, exit_y,   btn_w, btn_h)

        # ===== Game Over menu rects — ใช้ขนาดเดียวกับ pause =====
        self.go_menu_rect = pygame.Rect(
            GAME_WIDTH  // 2 - PW // 2,
            GAME_HEIGHT // 2 - PH // 2,
            PW, PH
        )
        go_exit_y  = self.go_menu_rect.y + 376
        go_retry_y = self.go_menu_rect.y + 210
        go_menu_y  = (go_retry_y + go_exit_y) // 2
        self.GOBTN_RETRY = pygame.Rect(cx - btn_w//2, go_retry_y, btn_w, btn_h)
        self.GOBTN_MENU  = pygame.Rect(cx - btn_w//2, go_menu_y,  btn_w, btn_h)
        self.GOBTN_EXIT  = pygame.Rect(cx - btn_w//2, go_exit_y,  btn_w, btn_h)

    # ------------------------------------------------------------------ #
    def _build_avatar(self, char_data):
        """สร้าง avatar surface วงกลม ขนาด 80px สำหรับใส่ใน HP/MP frame"""
        SIZE = 82
        portrait_raw = self.portraits.get(self._char_name)
        self._avatar_surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

        if portrait_raw:
            scaled = pygame.transform.smoothscale(portrait_raw, (SIZE, SIZE))
            # clip เป็นวงกลม
            mask = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.circle(mask, (255, 255, 255, 255), (SIZE//2, SIZE//2), SIZE//2)
            result = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
            result.blit(scaled, (0, 0))
            # apply circular mask
            for x in range(SIZE):
                for y in range(SIZE):
                    if mask.get_at((x, y))[3] == 0:
                        result.set_at((x, y), (0, 0, 0, 0))
            self._avatar_surf = result
        else:
            # fallback: สี solid ตามตัวละคร
            colors = {"Pig": (255, 182, 193), "Rabbit": (220, 210, 200), "Sheep": (240, 240, 240)}
            c = colors.get(self._char_name, (180, 180, 180))
            pygame.draw.circle(self._avatar_surf, c, (SIZE//2, SIZE//2), SIZE//2)

    # ------------------------------------------------------------------ #
    def _spawn_water_traps(self, count):
        self.water_traps = []
        attempts = 0
        while len(self.water_traps) < count and attempts < 500:
            attempts += 1
            rx, ry = random.randint(1, 24), random.randint(1, 18)
            if self.grid_data[ry][rx] == 0:
                self.water_traps.append(WaterTrap(rx * TILE_SIZE, ry * TILE_SIZE))

    def spawn_items_no_overlap(self):
        self.items_list = []
        self.stars_list = []
        item_types = [(HealItem, "heal.png"), (ShieldItem, "shield.png"),
                      (ClockItem, "clock.png"), (WallItem, "wall.png"), (TrapItem, "trap.png")]
        valid_tiles = [(c, r) for r in range(GRID_SIZE_Y) for c in range(GRID_SIZE_X)
                       if self.grid_data[r][c] == 0]
        chosen_locs = random.sample(valid_tiles, 15)
        idx = 0
        for cls, img in item_types:
            item_name = img.replace(".png", "")
            for _ in range(2):
                pos = chosen_locs[idx]
                it = cls(item_name, img, pos[0]*TILE_SIZE, pos[1]*TILE_SIZE)
                self.items_list.append(it)
                idx += 1
        for _ in range(5):
            pos = chosen_locs[idx]
            s = StarItem("star", "star.png", pos[0]*TILE_SIZE, pos[1]*TILE_SIZE)
            self.stars_list.append(s)
            idx += 1

    def is_walkable(self, px, py):
        margin, hb_size = 7, 20
        points = [(px+margin, py+margin), (px+margin+hb_size, py+margin),
                  (px+margin, py+margin+hb_size), (px+margin+hb_size, py+margin+hb_size)]
        for x, y in points:
            gx, gy = int(x // 30), int(y // 30)
            if not (0 <= gx < 26 and 0 <= gy < 20) or self.grid_data[gy][gx] != 0:
                return False
        return True

    # ------------------------------------------------------------------ #
    def _draw_wood_tile(self, x, y):
        """วาดบล็อกไม้สมจริง — ลายเสี้ยน + ข้อ + ไฮไลต์"""
        T = TILE_SIZE
        rect = pygame.Rect(x, y, T, T)

        # พื้นฐานไม้กลาง
        WOOD_BASE   = (160, 100, 45)
        WOOD_DARK2  = ( 95,  55, 18)
        WOOD_MID2   = (140,  85, 35)
        WOOD_GRAIN  = (175, 118, 58)
        WOOD_GRAIN2 = (125,  75, 28)
        WOOD_HI2    = (210, 155, 80)
        WOOD_EDGE   = ( 80,  45, 12)

        pygame.draw.rect(self.screen, WOOD_BASE, rect)

        # ลายเสี้ยนแนวตั้ง (grain lines) — วาด 3 เส้น สลับสี
        grain_xs = [x + T//5, x + T//2, x + T*4//5]
        for i, gx in enumerate(grain_xs):
            col = WOOD_GRAIN if i % 2 == 0 else WOOD_GRAIN2
            pygame.draw.line(self.screen, col, (gx, y+1), (gx, y+T-2), 1)

        # ลายเสี้ยนแนวนอนเบาๆ (cross grain)
        for gy_off in [T//4, T*3//4]:
            pygame.draw.line(self.screen, WOOD_GRAIN2,
                             (x+2, y+gy_off), (x+T-3, y+gy_off), 1)

        # ขอบบน-ซ้าย ไฮไลต์ (แสง)
        pygame.draw.line(self.screen, WOOD_HI2,  (x+1, y+1), (x+T-2, y+1),   2)
        pygame.draw.line(self.screen, WOOD_GRAIN, (x+1, y+1), (x+1,   y+T-2), 1)

        # ขอบล่าง-ขวา เงา (dark)
        pygame.draw.line(self.screen, WOOD_DARK2, (x+1,   y+T-2), (x+T-1, y+T-2), 2)
        pygame.draw.line(self.screen, WOOD_DARK2, (x+T-2, y+1),   (x+T-2, y+T-2), 2)

        # outline นอกสุด
        pygame.draw.rect(self.screen, WOOD_EDGE, rect, 1)

    # ------------------------------------------------------------------ #
    def _draw_stone_tile(self, x, y):
        """วาดบล็อกหินแบบเดิม"""
        T = TILE_SIZE
        rect = (x, y, T, T)
        pygame.draw.rect(self.screen, COLOR_WALL, rect)
        pygame.draw.line(self.screen, COLOR_WALL_LIGHT, (x, y), (x+T-2, y), 2)
        pygame.draw.line(self.screen, COLOR_WALL_LIGHT, (x, y), (x, y+T-2), 2)
        pygame.draw.line(self.screen, COLOR_WALL_DARK, (x+1, y+T-2), (x+T-1, y+T-2), 2)
        pygame.draw.line(self.screen, COLOR_WALL_DARK, (x+T-2, y+1), (x+T-2, y+T-1), 2)
        pygame.draw.line(self.screen, COLOR_WALL_DARK, (x+T//2, y+2), (x+T//2, y+T-4), 1)
        pygame.draw.line(self.screen, COLOR_WALL_DARK, (x+2, y+T//2), (x+T-4, y+T//2), 1)

    # ------------------------------------------------------------------ #
    def draw_world(self):
        map_rect = (MARGIN, UI_HEIGHT, TILE_SIZE * GRID_SIZE_X, TILE_SIZE * GRID_SIZE_Y)
        pygame.draw.rect(self.screen, COLOR_GRASS, map_rect)

        # วาดลายหญ้าเล็กน้อย (tile 0)
        for row in range(GRID_SIZE_Y):
            for col in range(GRID_SIZE_X):
                tile_type = self.grid_data[row][col]
                x, y = col * TILE_SIZE + MARGIN, row * TILE_SIZE + UI_HEIGHT

                if tile_type == 2:
                    self._draw_wood_tile(x, y)
                elif tile_type == 1:
                    self._draw_stone_tile(x, y)
                elif tile_type == 0:
                    # หญ้าจุดเล็กๆ สำหรับ texture
                    pygame.draw.circle(self.screen, COLOR_GRASS_LIGHT,
                                       (x + TILE_SIZE//2, y + TILE_SIZE//2), 2)

    # ------------------------------------------------------------------ #
    def draw_ui(self):
        """วาด HP/MP bar พร้อมกรอบไม้ + วงกลม avatar และ pause button"""

        # ---------- กรอบไม้สำหรับ HP/MP — ขยับซ้าย ----------
        FRAME_X  = 5          # ขยับซ้ายกว่าเดิม (เดิม MARGIN-10 = 30)
        FRAME_Y  = 15
        FRAME_W  = 310
        FRAME_H  = 108
        FRAME_R  = 18

        # ตัวกรอบ (ไม้กลาง) — ไม่มีเงา
        pygame.draw.rect(self.screen, WOOD_MID,
                         (FRAME_X, FRAME_Y, FRAME_W, FRAME_H), border_radius=FRAME_R)
        # ขอบนอก
        pygame.draw.rect(self.screen, WOOD_DARK,
                         (FRAME_X, FRAME_Y, FRAME_W, FRAME_H), 5, border_radius=FRAME_R)
        # ไฮไลต์บน
        pygame.draw.rect(self.screen, WOOD_HI,
                         (FRAME_X+14, FRAME_Y+6, FRAME_W-28, 8), border_radius=6)

        # ---------- วงกลมซ้าย (avatar) ----------
        CIRC_CX = FRAME_X + 52
        CIRC_CY = FRAME_Y + FRAME_H // 2
        CIRC_R  = 44

        # พื้นวงกลม (สีไม้เข้ม) — ไม่มีเงา
        pygame.draw.circle(self.screen, WOOD_DARK, (CIRC_CX, CIRC_CY), CIRC_R)
        # วงกลมชั้นใน (พื้นหลัง avatar)
        pygame.draw.circle(self.screen, (60, 40, 20), (CIRC_CX, CIRC_CY), CIRC_R - 5)

        # วาด avatar
        av = self._avatar_surf
        av_size = CIRC_R * 2 - 10
        av_scaled = pygame.transform.smoothscale(av, (av_size, av_size))
        self.screen.blit(av_scaled, (CIRC_CX - av_size//2, CIRC_CY - av_size//2))

        # ขอบวงกลม (ไม้อ่อน)
        pygame.draw.circle(self.screen, WOOD_LIGHT, (CIRC_CX, CIRC_CY), CIRC_R, 4)
        # ไฮไลต์ขอบบน
        pygame.draw.arc(self.screen, WOOD_HI,
                        (CIRC_CX - CIRC_R, CIRC_CY - CIRC_R, CIRC_R*2, CIRC_R*2),
                        math.radians(30), math.radians(150), 3)

        # ---------- HP bar ----------
        BAR_X   = FRAME_X + 108
        HP_Y    = FRAME_Y + 22
        BAR_W   = FRAME_W - 120
        BAR_H   = 30

        hp_color = (255, 255, 255) if self.player.is_shielded else COLOR_HP

        # เงา bar
        pygame.draw.rect(self.screen, (15, 8, 3), (BAR_X+2, HP_Y+2, BAR_W, BAR_H), border_radius=12)
        # พื้น bar
        pygame.draw.rect(self.screen, (40, 25, 12), (BAR_X, HP_Y, BAR_W, BAR_H), border_radius=12)
        # fill HP
        hp_fill = int(BAR_W * max(0, self.player.hp) / self.player.max_hp)
        if hp_fill > 0:
            pygame.draw.rect(self.screen, hp_color, (BAR_X, HP_Y, hp_fill, BAR_H), border_radius=12)
            # ไฮไลต์บน
            pygame.draw.rect(self.screen, (255, 100, 100) if not self.player.is_shielded else (200, 240, 255),
                             (BAR_X+2, HP_Y+3, max(0, hp_fill-4), BAR_H//3), border_radius=8)
        # ขอบ bar
        pygame.draw.rect(self.screen, WOOD_DARK, (BAR_X, HP_Y, BAR_W, BAR_H), 3, border_radius=12)

        hp_text = self.bar_font.render(f"HP  {int(self.player.hp)} / {self.player.max_hp}", True, (255, 245, 220))
        hp_sh   = self.bar_font.render(f"HP  {int(self.player.hp)} / {self.player.max_hp}", True, (20, 10, 5))
        self.screen.blit(hp_sh,   (BAR_X + 8, HP_Y + 5))
        self.screen.blit(hp_text, (BAR_X + 7, HP_Y + 4))

        # ---------- MP bar ----------
        MP_Y = HP_Y + BAR_H + 12

        pygame.draw.rect(self.screen, (15, 8, 3), (BAR_X+2, MP_Y+2, BAR_W, 22), border_radius=10)
        pygame.draw.rect(self.screen, (40, 25, 12), (BAR_X, MP_Y, BAR_W, 22), border_radius=10)
        mp_fill = int(BAR_W * self.player.mana / self.player.max_mana)
        if mp_fill > 0:
            pygame.draw.rect(self.screen, COLOR_MP, (BAR_X, MP_Y, mp_fill, 22), border_radius=10)
            pygame.draw.rect(self.screen, (100, 190, 255), (BAR_X+2, MP_Y+3, max(0, mp_fill-4), 7), border_radius=6)
        pygame.draw.rect(self.screen, WOOD_DARK, (BAR_X, MP_Y, BAR_W, 22), 3, border_radius=10)

        mp_text = self.bar_font.render(f"MP  {int(self.player.mana)} / {self.player.max_mana}", True, (200, 230, 255))
        mp_sh   = self.bar_font.render(f"MP  {int(self.player.mana)} / {self.player.max_mana}", True, (20, 10, 5))
        self.screen.blit(mp_sh,   (BAR_X + 8, MP_Y + 3))
        self.screen.blit(mp_text, (BAR_X + 7, MP_Y + 2))

        # ---------- SCORE — กลางระหว่าง title กับขวา ----------
        score_label = f"SCORE: {self.player.score}"
        if self.player.char_type == "Sheep":
            score_label += "  (x2)"

        sc_surf = self.font.render(score_label, True, COLOR_SCORE_TEXT)
        # center score ระหว่างกลางจอ (title) กับ pause button + ขยับขวา 10, ลง 3
        score_cx = (GAME_WIDTH // 2 + (GAME_WIDTH - self.PAUSE_BTN_R * 2 - 10)) // 2 + 70
        score_x  = score_cx + sc_surf.get_width() // 2
        score_y = 75
        # outline หนา — วาด 8 ทิศ + มุมทแยง radius 2
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0: continue
                out = self.font.render(score_label, True, COLOR_SCORE_OUTLINE)
                self.screen.blit(out, (score_x - out.get_width() + dx, score_y + dy))
        self.screen.blit(sc_surf, (score_x - sc_surf.get_width(), score_y))

        # ---------- Pause Button — วงกลมขนาดเล็ก ชิดขวา ----------
        mx, my = pygame.mouse.get_pos()
        cx, cy, r = self.PAUSE_BTN_CX, self.PAUSE_BTN_CY, self.PAUSE_BTN_R
        hover = math.hypot(mx - cx, my - cy) <= r

        # ตัววงกลม (ไม่มีเงา)
        fill_c = (235, 190, 55) if hover else (215, 165, 40)
        pygame.draw.circle(self.screen, fill_c, (cx, cy), r)
        # ขอบน้ำตาลเท่านั้น — ไม่มี arc ไฮไลต์
        pygame.draw.circle(self.screen, WOOD_DARK, (cx, cy), r, 4)

        # สัญลักษณ์ pause (|| สองแท่ง)
        bar_h = int(r * 0.85)
        bar_w = max(5, int(r * 0.22))
        gap   = max(4, int(r * 0.18))
        bx1   = cx - gap - bar_w
        bx2   = cx + gap
        by    = cy - bar_h // 2
        for bx in (bx1, bx2):
            # เงา
            pygame.draw.rect(self.screen, (30, 18, 6),
                             (bx+2, by+2, bar_w, bar_h), border_radius=3)
            # แท่ง
            pygame.draw.rect(self.screen, WOOD_DARK,
                             (bx, by, bar_w, bar_h), border_radius=3)
            # ไฮไลต์
            pygame.draw.rect(self.screen, WOOD_HI,
                             (bx+2, by+2, bar_w-4, bar_h//3), border_radius=2)

        # ---------- Flash เลือดต่ำ ----------
        if self.player.hp < 50:
            s = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
            self.flash_alpha += 5 * self.flash_dir
            if self.flash_alpha >= 100 or self.flash_alpha <= 0:
                self.flash_dir *= -1
            pygame.draw.rect(s, (255, 0, 0, self.flash_alpha),
                             (0, 0, GAME_WIDTH, GAME_HEIGHT), 15)
            self.screen.blit(s, (0, 0))

    # ------------------------------------------------------------------ #
    def draw_pause_menu(self):
        """วาด pause overlay และปุ่ม 3 ปุ่มบนกลางหน้าจอ"""
        mx, my = pygame.mouse.get_pos()

        # dim overlay
        dim = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        self.screen.blit(dim, (0, 0))

        r = self.pause_menu_rect
        PW, PH = r.width, r.height

        if self.pause_panel:
            # scale pause.png ให้พอดีกับ rect
            panel_scaled = pygame.transform.smoothscale(self.pause_panel, (PW, PH))
            self.screen.blit(panel_scaled, (r.x, r.y))
        else:
            # fallback: วาดกรอบไม้เอง
            pygame.draw.rect(self.screen, (20, 12, 4), r.move(6, 6), border_radius=22)
            pygame.draw.rect(self.screen, WOOD_MID, r, border_radius=22)
            pygame.draw.rect(self.screen, WOOD_DARK, r, 6, border_radius=22)
            pygame.draw.rect(self.screen, WOOD_HI,
                             (r.x+18, r.y+10, PW-36, 10), border_radius=7)

            # หัวข้อ PAUSE
            title = self.pause_font.render("PAUSE", True, (255, 230, 80))
            tsh   = self.pause_font.render("PAUSE", True, (80, 50, 10))
            tx = r.centerx - title.get_width()//2
            self.screen.blit(tsh,   (tx+2, r.y+28))
            self.screen.blit(title, (tx,   r.y+26))

        # ปุ่ม 3 ปุ่ม
        _draw_wood_btn_game(self.screen, self.PBTN_RESUME, "RESUME",
                            self.pause_font, style="green",
                            hover=self.PBTN_RESUME.collidepoint((mx, my)))
        _draw_wood_btn_game(self.screen, self.PBTN_MENU,   "MAIN MENU",
                            self.pause_font, style="gold",
                            hover=self.PBTN_MENU.collidepoint((mx, my)),
                            font_small=self.pause_font_small)
        _draw_wood_btn_game(self.screen, self.PBTN_EXIT,   "EXIT",
                            self.pause_font, style="red",
                            hover=self.PBTN_EXIT.collidepoint((mx, my)))

    # ------------------------------------------------------------------ #
    def draw_gameover_menu(self):
        """วาด game over overlay พร้อมปุ่ม RETRY / MAIN MENU / EXIT"""
        mx, my = pygame.mouse.get_pos()

        dim = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.screen.blit(dim, (0, 0))

        r = self.go_menu_rect
        PW, PH = r.width, r.height

        if self.gameover_panel:
            panel_scaled = pygame.transform.smoothscale(self.gameover_panel, (PW, PH))
            self.screen.blit(panel_scaled, (r.x, r.y))
        else:
            # fallback panel
            pygame.draw.rect(self.screen, (20, 12, 4), r.move(6, 6), border_radius=22)
            pygame.draw.rect(self.screen, WOOD_MID, r, border_radius=22)
            pygame.draw.rect(self.screen, WOOD_DARK, r, 6, border_radius=22)
            title = self.pause_font.render("GAME OVER", True, (255, 60, 60))
            tsh   = self.pause_font.render("GAME OVER", True, (80, 10, 10))
            tx = r.centerx - title.get_width()//2
            self.screen.blit(tsh,   (tx+2, r.y+28))
            self.screen.blit(title, (tx,   r.y+26))

        _draw_wood_btn_game(self.screen, self.GOBTN_RETRY, "RETRY",
                            self.pause_font, style="green",
                            hover=self.GOBTN_RETRY.collidepoint((mx, my)))
        _draw_wood_btn_game(self.screen, self.GOBTN_MENU,  "MAIN MENU",
                            self.pause_font, style="gold",
                            hover=self.GOBTN_MENU.collidepoint((mx, my)),
                            font_small=self.pause_font_small)
        _draw_wood_btn_game(self.screen, self.GOBTN_EXIT,  "EXIT",
                            self.pause_font, style="red",
                            hover=self.GOBTN_EXIT.collidepoint((mx, my)))

    # ------------------------------------------------------------------ #
    def draw(self):
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill(COLOR_BG_MAIN)

        self.draw_world()
        offset = (MARGIN, UI_HEIGHT)
        for wt in self.water_traps: wt.draw(self.screen, offset)
        for tp in self.active_traps:
            self.screen.blit(tp.image, (tp.pos[0]+MARGIN, tp.pos[1]+UI_HEIGHT))
        for it in self.items_list + self.stars_list:
            if it.is_active:
                self.screen.blit(it.image, (it.pos[0]+MARGIN, it.pos[1]+UI_HEIGHT))

        self.player.draw(self.screen, offset)
        self.wolf.draw(self.screen, offset)
        self.draw_ui()

        if self.game_over:
            self.draw_gameover_menu()
        elif self.paused:
            self.draw_pause_menu()

        pygame.display.flip()

    # ------------------------------------------------------------------ #
    def update(self):
        if self.paused:
            return  # หยุด update ขณะ pause

        if self.game_over:
            return  # รอ click ปุ่มใน draw_gameover_menu

        self.player.move()
        self.player.check_boundaries(self)
        self.player.update_timers(self)
        if self.wolf.update(self.player, self):
            self.stats.log_damage(self.player, self.wolf)
        self.stats.auto_record(self.player, self.wolf)
        self.wolf.speed = self.wolf.base_speed + (self.player.score // 10) * 0.2
        self.water_relocate_timer += 1
        if self.water_relocate_timer >= 600:
            self.water_relocate_timer = 0
            self._spawn_water_traps(len(self.water_traps))
        score_threshold = (self.player.score // 20) * 20
        if score_threshold > self.last_water_score_threshold and self.player.score >= 20:
            self.last_water_score_threshold = score_threshold
            new_count = self.BASE_WATER_COUNT + (score_threshold // 20)
            if len(self.water_traps) < new_count:
                self._spawn_water_traps(new_count)
        p_cx = self.player.pos[0] + 17
        p_cy = self.player.pos[1] + 17
        for it in self.items_list + self.stars_list:
            if it.is_active:
                if math.hypot(p_cx - (it.pos[0]+13), p_cy - (it.pos[1]+13)) < 18:
                    if isinstance(it, TrapItem): it.on_collect(self.player, self.wolf)
                    else: it.on_collect(self.player)
                    self.stats.log_item_collect(self.player, self.wolf, it.item_type)
            elif it.respawn_timer():
                it.spawn(self.grid_data)
        if self.player.pending_trap_timer == 1:
            self.active_traps.append(PlacedTrap(self.player.pos[0]+3, self.player.pos[1]+3))
        w_cx = self.wolf.pos[0] + 20
        w_cy = self.wolf.pos[1] + 20
        for tp in self.active_traps[:]:
            tp.timer -= 1
            if math.hypot(w_cx - (tp.pos[0]+14), w_cy - (tp.pos[1]+14)) < 22:
                self.wolf.slow_timer = 180
                self.active_traps.remove(tp)
            elif tp.timer <= 0:
                self.active_traps.remove(tp)
        for wt in self.water_traps:
            if math.hypot(p_cx - (wt.pos[0]+15), p_cy - (wt.pos[1]+15)) < 22:
                self.player.apply_water_effect()
        if self.player.hp <= 0:
            self.player.hp = 0
            if not self.game_over:
                self.stats.log_game_over(self.player, self.wolf)
            self.game_over = True

    # ------------------------------------------------------------------ #
    def run(self):
        while True:
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # ปุ่มใน game over menu
                    if self.game_over:
                        if self.GOBTN_RETRY.collidepoint((mx, my)):
                            return "SELECT"   # กลับหน้าเลือกตัวละคร
                        elif self.GOBTN_MENU.collidepoint((mx, my)):
                            return "MENU"
                        elif self.GOBTN_EXIT.collidepoint((mx, my)):
                            pygame.quit(); sys.exit()

                    # คลิกปุ่ม Pause (วงกลม)
                    if not self.game_over:
                        cx, cy, r = self.PAUSE_BTN_CX, self.PAUSE_BTN_CY, self.PAUSE_BTN_R
                        if math.hypot(mx - cx, my - cy) <= r:
                            self.paused = not self.paused

                    # ปุ่มใน pause menu
                    if self.paused:
                        if self.PBTN_RESUME.collidepoint((mx, my)):
                            self.paused = False
                        elif self.PBTN_MENU.collidepoint((mx, my)):
                            return "MENU"   # กลับหน้าหลัก
                        elif self.PBTN_EXIT.collidepoint((mx, my)):
                            pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not self.game_over:
                        self.paused = not self.paused

            self.update()
            self.draw()
            self.clock.tick(60)