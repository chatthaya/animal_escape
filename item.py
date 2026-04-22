import pygame
import random
import time

ITEM_SIZE = 28  # พอดีกับทางเดิน 30px

class Item:
    def __init__(self, item_type, image_file, x=0, y=0):
        self.item_type = item_type
        self.pos = [x, y]
        self.is_active = True
        self.respawn_start_time = 0
        try:
            raw = pygame.image.load(image_file).convert_alpha()
            # โหลดในขนาดใหญ่ก่อน แล้ว smoothscale ลงมา → ภาพคมชัดกว่า scale ตรงๆ
            big = pygame.transform.smoothscale(raw, (ITEM_SIZE * 3, ITEM_SIZE * 3))
            self.image = pygame.transform.smoothscale(big, (ITEM_SIZE, ITEM_SIZE))
        except:
            self.image = pygame.Surface((ITEM_SIZE, ITEM_SIZE), pygame.SRCALPHA)
            self.image.fill((200, 200, 0))

    def spawn(self, map_data):
        while True:
            rx, ry = random.randint(1, 24), random.randint(1, 18)
            if map_data[ry][rx] == 0:
                self.pos = [rx * 30, ry * 30]
                self.is_active = True
                break

    def respawn_timer(self):
        if not self.is_active:
            if time.time() - self.respawn_start_time >= 2:
                return True
        return False

    def on_collect(self, player):
        self.is_active = False
        self.respawn_start_time = time.time()

class HealItem(Item):
    def on_collect(self, player):
        player.hp = min(player.max_hp, player.hp + 20)
        super().on_collect(player)

class ShieldItem(Item):
    def on_collect(self, player):
        player.is_shielded = True
        super().on_collect(player)

class ClockItem(Item):
    def on_collect(self, player):
        player.speed_boost_timer = 120
        super().on_collect(player)

class WallItem(Item):
    def on_collect(self, player):
        player.is_wall_phasing = True
        player.wall_phase_timer = 60
        super().on_collect(player)

class StarItem(Item):
    def on_collect(self, player):
        # ใช้ add_score เพื่อให้แกะได้คะแนนคูณสอง
        player.add_score(1)
        super().on_collect(player)
        
class PlacedTrap:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.timer = 300
        try:
            raw = pygame.image.load("trap.png").convert_alpha()
            big = pygame.transform.smoothscale(raw, (84, 84))
            self.image = pygame.transform.smoothscale(big, (28, 28))
        except:
            self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
            self.image.fill((255, 0, 0))
            
class TrapItem(Item):
    def on_collect(self, player, enemy=None):
        # ไม่ slow หมาป่าทันที — slow จะเกิดเมื่อหมาป่าเดินผ่านกับดักที่วางไว้
        player.pending_trap_timer = 60
        self.is_active = False
        self.respawn_start_time = time.time()


class WaterTrap:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.color = (0, 191, 255, 150)
    def draw(self, surface, render_offset):
        draw_pos = (int(self.pos[0] + render_offset[0] + 15), int(self.pos[1] + render_offset[1] + 15))
        pygame.draw.circle(surface, self.color, draw_pos, 15)