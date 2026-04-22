import pygame
import random
import math
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

# สีใหม่สำหรับคะแนน
COLOR_SCORE_TEXT = (255, 255, 255)  # สีขาว
COLOR_SCORE_OUTLINE = (101, 67, 33) # สีน้ำตาล

class Game:
    def __init__(self, char_data):
        pygame.init()
        self.screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
        
        # --- โหลดภาพพื้นหลัง bg.jpg ---
        try:
            self.bg_image = pygame.image.load("bg.jpg").convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (GAME_WIDTH, GAME_HEIGHT))
        except:
            self.bg_image = None
            print("Warning: bg.jpg not found")
        # ----------------------------

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Verdana", 24, bold=True)
        self.bar_font = pygame.font.SysFont("Verdana", 16, bold=True)
        self.flash_alpha = 0
        self.flash_dir = 1
        self.all_occupied_positions = set()
        
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
        self.wolf = Wolf()
        self.game_over = False
        self.active_traps = []
        self.water_traps = []
        self.stats = StatsLogger(char_data["name"])
        self.water_relocate_timer = 0          
        self.last_water_score_threshold = 0    
        self.BASE_WATER_COUNT = 3              
        self.spawn_items_no_overlap()
        self._spawn_water_traps(self.BASE_WATER_COUNT)
    
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
        valid_tiles = [(c, r) for r in range(GRID_SIZE_Y) for c in range(GRID_SIZE_X) if self.grid_data[r][c] == 0]
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
            if not (0 <= gx < 26 and 0 <= gy < 20) or self.grid_data[gy][gx] != 0: return False
        return True

    def draw_world(self):
        map_rect = (MARGIN, UI_HEIGHT, TILE_SIZE * GRID_SIZE_X, TILE_SIZE * GRID_SIZE_Y)
        pygame.draw.rect(self.screen, COLOR_GRASS, map_rect)
        for row in range(GRID_SIZE_Y):
            for col in range(GRID_SIZE_X):
                tile_type = self.grid_data[row][col]
                x, y = col * TILE_SIZE + MARGIN, row * TILE_SIZE + UI_HEIGHT
                rect = (x, y, TILE_SIZE, TILE_SIZE)
                if tile_type == 2:
                    pygame.draw.rect(self.screen, COLOR_BORDER, rect)
                    pygame.draw.line(self.screen, COLOR_BORDER_DARK, (x, y+TILE_SIZE-2), (x+TILE_SIZE, y+TILE_SIZE-2), 2)
                    pygame.draw.line(self.screen, COLOR_BORDER_DARK, (x+TILE_SIZE-2, y), (x+TILE_SIZE-2, y+TILE_SIZE), 2)
                elif tile_type == 1:
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                    pygame.draw.line(self.screen, COLOR_WALL_LIGHT, (x, y), (x+TILE_SIZE-2, y), 2)
                    pygame.draw.line(self.screen, COLOR_WALL_DARK, (x+1, y+TILE_SIZE-2), (x+TILE_SIZE-1, y+TILE_SIZE-2), 2)
                elif tile_type == 0:
                    pygame.draw.rect(self.screen, COLOR_GRASS_LIGHT, (x+13, y+13, 4, 4))

    def draw_ui(self):
        # วาดแถบ HP/MP
        bar_x, bar_y = MARGIN, 40
        bar_w, bar_h = 250, 30
        hp_color = (255, 255, 255) if self.player.is_shielded else COLOR_HP
        pygame.draw.rect(self.screen, COLOR_BAR_BG, (bar_x, bar_y, bar_w, bar_h))
        hp_w = bar_w * (max(0, self.player.hp) / self.player.max_hp)
        pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, hp_w, bar_h))
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), 2)
        hp_text = self.bar_font.render(f"HP: {int(self.player.hp)} / {self.player.max_hp}", True, COLOR_TEXT_HP)
        self.screen.blit(hp_text, (bar_x + 10, bar_y + 4))

        pygame.draw.rect(self.screen, COLOR_BAR_BG, (bar_x, bar_y + 40, bar_w, 20))
        mp_w = bar_w * (self.player.mana / self.player.max_mana)
        pygame.draw.rect(self.screen, COLOR_MP, (bar_x, bar_y + 40, mp_w, 20))
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y + 40, bar_w, 20), 2)
        mp_text = self.bar_font.render(f"MP: {int(self.player.mana)} / {self.player.max_mana}", True, (255, 255, 255))
        self.screen.blit(mp_text, (bar_x + 10, bar_y + 40))

        # --- วาดคะแนน (สีขาว ขอบน้ำตาล) ---
        score_label = f"SCORE: {self.player.score}"
        if self.player.char_type == "Sheep": score_label += " (x2)"
        
        # วาดขอบน้ำตาล (วาด 8 ทิศทางรอบตัวอักษร)
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
            outline_surf = self.font.render(score_label, True, COLOR_SCORE_OUTLINE)
            out_x = GAME_WIDTH - MARGIN - outline_surf.get_width() + dx
            self.screen.blit(outline_surf, (out_x, 50 + dy))
            
        # วาดตัวอักษรสีขาวทับหน้า
        score_surf = self.font.render(score_label, True, COLOR_SCORE_TEXT)
        self.screen.blit(score_surf, (GAME_WIDTH - MARGIN - score_surf.get_width(), 50))

        if self.player.hp < 50:
            s = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
            self.flash_alpha += 5 * self.flash_dir
            if self.flash_alpha >= 100 or self.flash_alpha <= 0: self.flash_dir *= -1
            pygame.draw.rect(s, (255, 0, 0, self.flash_alpha), (0, 0, GAME_WIDTH, GAME_HEIGHT), 15)
            self.screen.blit(s, (0,0))
            
    def draw(self):
        if self.bg_image: self.screen.blit(self.bg_image, (0, 0))
        else: self.screen.fill(COLOR_BG_MAIN)
            
        self.draw_world()
        offset = (MARGIN, UI_HEIGHT)
        for wt in self.water_traps: wt.draw(self.screen, offset)
        for tp in self.active_traps: self.screen.blit(tp.image, (tp.pos[0] + MARGIN, tp.pos[1] + UI_HEIGHT))
        for it in self.items_list + self.stars_list:
            if it.is_active: self.screen.blit(it.image, (it.pos[0] + MARGIN, it.pos[1] + UI_HEIGHT))

        if self.game_over:
            overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            msg = self.font.render("GAME OVER", True, (255, 0, 0))
            sub_msg = self.bar_font.render("Press SPACE to Restart", True, (255, 255, 255))
            self.screen.blit(msg, (GAME_WIDTH//2 - msg.get_width()//2, GAME_HEIGHT//2 - 20))
            self.screen.blit(sub_msg, (GAME_WIDTH//2 - sub_msg.get_width()//2, GAME_HEIGHT//2 + 30))
        
        self.player.draw(self.screen, offset)
        self.wolf.draw(self.screen, offset)
        self.draw_ui()
        pygame.display.flip()

    def update(self):
        if self.game_over:
            if pygame.key.get_pressed()[pygame.K_SPACE]: return "RESTART"
            return
        self.player.move()
        self.player.check_boundaries(self)
        self.player.update_timers(self)
        if self.wolf.update(self.player, self): self.stats.log_damage(self.player, self.wolf)
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
            if len(self.water_traps) < new_count: self._spawn_water_traps(new_count)
        p_cx, p_cy = self.player.pos[0] + 17, self.player.pos[1] + 17
        for it in self.items_list + self.stars_list:
            if it.is_active:
                if math.hypot(p_cx - (it.pos[0]+13), p_cy - (it.pos[1]+13)) < 18:
                    if isinstance(it, TrapItem): it.on_collect(self.player, self.wolf)
                    else: it.on_collect(self.player)
                    self.stats.log_item_collect(self.player, self.wolf, it.item_type)
            elif it.respawn_timer(): it.spawn(self.grid_data)
        if self.player.pending_trap_timer == 1:
            self.active_traps.append(PlacedTrap(self.player.pos[0]+3, self.player.pos[1]+3))
        w_cx, w_cy = self.wolf.pos[0] + 20, self.wolf.pos[1] + 20
        for tp in self.active_traps[:]:
            tp.timer -= 1
            if math.hypot(w_cx - (tp.pos[0]+14), w_cy - (tp.pos[1]+14)) < 22:
                self.wolf.slow_timer = 180
                self.active_traps.remove(tp)
            elif tp.timer <= 0: self.active_traps.remove(tp)
        for wt in self.water_traps:
            if math.hypot(p_cx - (wt.pos[0]+15), p_cy - (wt.pos[1]+15)) < 22: self.player.apply_water_effect()
        if self.player.hp <= 0:
            self.player.hp = 0
            if not self.game_over: self.stats.log_game_over(self.player, self.wolf)
            self.game_over = True
                
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
            res = self.update()
            if res == "RESTART": return
            self.draw()
            self.clock.tick(60)