import pygame
import math
import heapq

WOLF_SIZE = 30

class Wolf:
    def __init__(self):
        self.base_speed = 1
        self.speed = self.base_speed
        self.pos = [30.0, 30.0]
        self.slow_timer = 0
        self.stun_timer = 0
        
        try:
            raw = pygame.image.load("wolf.png").convert_alpha()
            big = pygame.transform.smoothscale(raw, (WOLF_SIZE * 3, WOLF_SIZE * 3))
            self.img_right = pygame.transform.smoothscale(big, (WOLF_SIZE, WOLF_SIZE))
            self.img_left = pygame.transform.flip(self.img_right, True, False)
            self.image = self.img_right
        except:
            self.image = pygame.Surface((WOLF_SIZE, WOLF_SIZE), pygame.SRCALPHA)
            self.image.fill((150, 0, 0))

    def _draw_outline(self, surface, image, x, y, color, thickness=3):
        """วาด outline รอบรูปด้วยการ blit รูปเดิมหลายทิศทาง"""
        mask = pygame.mask.from_surface(image)
        outline_surf = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
        outline_surf.set_colorkey((0, 0, 0))
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx == 0 and dy == 0:
                    continue
                if dx * dx + dy * dy <= thickness * thickness:
                    surface.blit(outline_surf, (x + dx, y + dy))

    def calculate_astar_path(self, start, target, grid):
        def heuristic(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
        neighbors = [(0,1),(0,-1),(1,0),(-1,0)]
        oheap = []
        heapq.heappush(oheap, (0, start))
        came_from = {}
        g_score = {start: 0}
        
        while oheap:
            current = heapq.heappop(oheap)[1]
            if current == target:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path
            
            for i, j in neighbors:
                neighbor = (current[0] + i, current[1] + j)
                if 0 <= neighbor[0] < 26 and 0 <= neighbor[1] < 20:
                    if grid[neighbor[1]][neighbor[0]] == 0:
                        temp_g = g_score[current] + 1
                        if temp_g < g_score.get(neighbor, float('inf')):
                            came_from[neighbor] = current
                            g_score[neighbor] = temp_g
                            f_score = temp_g + heuristic(neighbor, target)
                            heapq.heappush(oheap, (f_score, neighbor))
        return []

    def update(self, player, map_manager):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return # หยุดนิ่งถ้าติดสตัน
        
        start_g = (int((self.pos[0]+16)//30), int((self.pos[1]+16)//30))
        target_g = (int((player.pos[0]+15)//30), int((player.pos[1]+15)//30))
        
        curr_speed = self.speed
        if self.slow_timer > 0:
            self.slow_timer -= 1
            curr_speed *= 0.4

        path = self.calculate_astar_path(start_g, target_g, map_manager.grid_data)
        if path:
            next_step = path[-1]
            tx, ty = next_step[0]*30, next_step[1]*30
            dx, dy = tx - self.pos[0], ty - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist > 2:
                self.pos[0] += (dx/dist) * curr_speed
                self.pos[1] += (dy/dist) * curr_speed
                self.image = self.img_right if dx > 0 else self.img_left

        # โจมตีเมื่อใกล้ผู้เล่น
        dist = math.hypot(self.pos[0]-player.pos[0], self.pos[1]-player.pos[1])
        if dist < 28:
            if player.is_shielded:
                damaged = player.take_damage(25)
                if damaged:
                    player.is_shielded = False
                    self.stun_timer = 120
                    return True   # ← แจ้ง map_manager ว่ามีดาเมจ
            else:
                damaged = player.take_damage(50)
                if damaged:
                    return True   # ← แจ้ง map_manager ว่ามีดาเมจ
        return False
            
    def draw(self, surface, offset):
        x, y = int(self.pos[0] + offset[0]), int(self.pos[1] + offset[1])
        # วาด outline ล้อมรอบรูปหมาป่าแทนกรอบสี่เหลี่ยม
        if self.stun_timer > 0:
            self._draw_outline(surface, self.image, x, y, (255, 220, 0), thickness=3)
        elif self.slow_timer > 0:
            self._draw_outline(surface, self.image, x, y, (255, 255, 255), thickness=2)
        surface.blit(self.image, (x, y))