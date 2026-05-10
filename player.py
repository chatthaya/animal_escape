import pygame
import math

SPRITE_SIZE = 28     
HITBOX_MARGIN = 5   

class Player:
    def __init__(self, char_data):
        self.char_type = char_data["name"]
        self.max_hp = char_data.get("hp", 200)
        self.hp = self.max_hp
        self.max_mana = char_data.get("mp", 50)
        self.mana = self.max_mana
        self.water_slow_timer = 0
        
        self.base_speed = 3
        self.speed = self.base_speed
        self.score = 0
        
        self.pos = [13 * 30, 9 * 30] 
        self.vel = [0, 0]
        
        self.is_shielded = False
        self.is_wall_phasing = False
        self.wall_phase_timer = 0
        self.pending_trap_timer = 0
        self.speed_boost_timer = 0
        self.invulnerable_timer = 0
        self.regen_timer = 0
        
        raw = pygame.image.load(char_data["img_file"]).convert_alpha()
        big = pygame.transform.smoothscale(raw, (SPRITE_SIZE * 3, SPRITE_SIZE * 3))
        self.img_right = pygame.transform.smoothscale(big, (SPRITE_SIZE, SPRITE_SIZE))
        self.img_left = pygame.transform.flip(self.img_right, True, False)
        self.image = self.img_right

    def apply_water_effect(self):
        self.water_slow_timer = 30
        if self.invulnerable_timer <= 0:
            if self.is_shielded:
                self.is_shielded = False
            else:
                self.hp -= 10
            self.invulnerable_timer = 60
            
    def move(self):
        keys = pygame.key.get_pressed()
        self.vel = [0, 0]
        
        current_speed = self.speed
        if self.speed_boost_timer > 0:
            current_speed = self.base_speed * 2
        
        if self.water_slow_timer > 0:
            current_speed *= 0.4
            self.water_slow_timer -= 1
            
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel[0] = -current_speed
            self.image = self.img_left
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel[0] = current_speed
            self.image = self.img_right
            
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.vel[1] = -current_speed
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.vel[1] = current_speed

        if keys[pygame.K_LSHIFT] and self.mana > 0:
            self.vel[0] *= 1.5
            self.vel[1] *= 1.5
            self.mana -= 0.5
        else:
            if self.mana < self.max_mana:
                self.mana += 0.1

    def take_damage(self, amount):
        if self.invulnerable_timer <= 0:
            self.hp -= amount
            self.invulnerable_timer = 120 
            return True
        return False

    def use_item(self, item_type):
        if item_type == "heal":
            self.hp = min(self.max_hp, self.hp + 20)
        elif item_type == "shield":
            self.is_shielded = True
        elif item_type == "clock":
            self.speed_boost_timer = 120
        elif item_type == "wall":
            self.is_wall_phasing = True
            self.wall_phase_timer = 60

    def check_boundaries(self, map_manager):
        vx, vy = self.vel[0], self.vel[1]
        if vx == 0 and vy == 0:
            return

        m  = HITBOX_MARGIN
        hs = SPRITE_SIZE - m * 2   
        TILE = 30
        SNAP_TOL = 6

        def tile_at(px, py):
            gx, gy = int(px // TILE), int(py // TILE)
            if 0 <= gx < 26 and 0 <= gy < 20:
                return map_manager.grid_data[gy][gx]
            return 2

        def corners_ok(nx, ny, allowed=(0,)):
            for px, py in [
                (nx + m,      ny + m),
                (nx + m + hs, ny + m),
                (nx + m,      ny + m + hs),
                (nx + m + hs, ny + m + hs),
            ]:
                if tile_at(px, py) not in allowed:
                    return False
            return True

        if self.is_wall_phasing:
            new_x = self.pos[0] + vx
            new_y = self.pos[1] + vy
            if corners_ok(new_x, new_y, allowed=(0, 1)):
                self.pos[0], self.pos[1] = new_x, new_y
            return

        new_x = self.pos[0] + vx
        new_y = self.pos[1] + vy

        if corners_ok(new_x, new_y):
            self.pos[0], self.pos[1] = new_x, new_y
            return

        moved = False
        if vx != 0 and corners_ok(new_x, self.pos[1]):
            self.pos[0] = new_x
            moved = True
        if vy != 0 and corners_ok(self.pos[0], new_y):
            self.pos[1] = new_y
            moved = True

        if moved:
            return

        if vx != 0 and not corners_ok(new_x, self.pos[1]):
            cx = self.pos[0] + m + hs / 2
            cy = self.pos[1] + m + hs / 2
            tile_row_center = (int(cy // TILE)) * TILE + TILE / 2
            offset_y = tile_row_center - cy
            if abs(offset_y) <= SNAP_TOL:
                snapped_y = self.pos[1] + offset_y
                if corners_ok(new_x, snapped_y):
                    self.pos[0] = new_x
                    self.pos[1] = snapped_y
                    return

        if vy != 0 and not corners_ok(self.pos[0], new_y):
            cx = self.pos[0] + m + hs / 2
            cy = self.pos[1] + m + hs / 2
            tile_col_center = (int(cx // TILE)) * TILE + TILE / 2
            offset_x = tile_col_center - cx
            if abs(offset_x) <= SNAP_TOL:
                snapped_x = self.pos[0] + offset_x
                if corners_ok(snapped_x, new_y):
                    self.pos[0] = snapped_x
                    self.pos[1] = new_y
                    return

    def push_out_of_wall(self, map_manager):
        m  = HITBOX_MARGIN
        hs = SPRITE_SIZE - m * 2

        def corners_in_wall():
            corners = [
                (self.pos[0] + m,      self.pos[1] + m),
                (self.pos[0] + m + hs, self.pos[1] + m),
                (self.pos[0] + m,      self.pos[1] + m + hs),
                (self.pos[0] + m + hs, self.pos[1] + m + hs),
            ]
            for px, py in corners:
                gx, gy = int(px // 30), int(py // 30)
                if 0 <= gx < 26 and 0 <= gy < 20:
                    if map_manager.grid_data[gy][gx] != 0:
                        return True
            return False

        if not corners_in_wall():
            return

        cx = int((self.pos[0] + SPRITE_SIZE // 2) // 30)
        cy = int((self.pos[1] + SPRITE_SIZE // 2) // 30)

        for r in range(1, 10):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if abs(dx) != r and abs(dy) != r:
                        continue  
                    nx, ny = cx + dx, cy + dy
                    if not (0 <= nx < 26 and 0 <= ny < 20):
                        continue
                    if map_manager.grid_data[ny][nx] != 0:
                        continue
                    tx = nx * 30 + (30 - SPRITE_SIZE) // 2
                    ty = ny * 30 + (30 - SPRITE_SIZE) // 2
                    ok = True
                    for px, py in [
                        (tx + m,      ty + m),
                        (tx + m + hs, ty + m),
                        (tx + m,      ty + m + hs),
                        (tx + m + hs, ty + m + hs),
                    ]:
                        gx2, gy2 = int(px // 30), int(py // 30)
                        if not (0 <= gx2 < 26 and 0 <= gy2 < 20) or map_manager.grid_data[gy2][gx2] != 0:
                            ok = False
                            break
                    if ok:
                        self.pos = [float(tx), float(ty)]
                        return
                        
    def update_timers(self, map_manager):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        
        if self.wall_phase_timer > 0:
            self.wall_phase_timer -= 1
            if self.wall_phase_timer == 0:
                self.is_wall_phasing = False
                self.push_out_of_wall(map_manager)
        
        if self.speed_boost_timer > 0: self.speed_boost_timer -= 1
        if self.pending_trap_timer > 0: self.pending_trap_timer -= 1

        if self.invulnerable_timer <= 0 and self.hp < self.max_hp:
            self.regen_timer += 1
            if self.regen_timer >= 60:
                self.hp = min(self.max_hp, self.hp + 1)
                self.regen_timer = 0 
        else:
            self.regen_timer = 0

    def add_score(self, amount):
        if self.char_type == "Sheep":
            self.score += amount * 2
        else:
            self.score += amount

    def draw(self, surface, offset):
        if self.invulnerable_timer % 10 < 5:
            surface.blit(self.image, (self.pos[0] + offset[0], self.pos[1] + offset[1]))