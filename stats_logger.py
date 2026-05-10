import csv
import os
import time
import math

CSV_FILE = "stats.csv"

FIELDNAMES = [
    "timestamp",        
    "event",            
    "char_type",        
    "score",            
    "hp",               
    "mana",             
    "player_x",         
    "player_y",        
    "enemy_x",          
    "enemy_y",          
    "enemy_dist",       
    "item_type",        
    "survival_time",    
]


class StatsLogger:
    def __init__(self, char_type):
        self.char_type = char_type
        self.log_buffer = []
        self.start_time = time.time()
        self.frame_timer = 0         
        self.survival_time = 0.0

        if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()

    def _survival_sec(self):
        return round(time.time() - self.start_time, 2)

    def _build_row(self, event, player, enemy, item_type=""):
        dist = math.hypot(player.pos[0] - enemy.pos[0], player.pos[1] - enemy.pos[1])
        return {
            "timestamp":     round(self._survival_sec(), 2),
            "event":         event,
            "char_type":     self.char_type,
            "score":         player.score,
            "hp":            round(player.hp, 1),
            "mana":          round(player.mana, 1),
            "player_x":      round(player.pos[0], 1),
            "player_y":      round(player.pos[1], 1),
            "enemy_x":       round(enemy.pos[0], 1),
            "enemy_y":       round(enemy.pos[1], 1),
            "enemy_dist":    round(dist, 1),
            "item_type":     item_type,
            "survival_time": round(self._survival_sec(), 2),
        }



    def log_item_collect(self, player, enemy, item_type):
        clean_type = str(item_type).replace(".png", "")
        self.log_buffer.append(self._build_row("item_collect", player, enemy, clean_type))

    def log_damage(self, player, enemy):
        self.log_buffer.append(self._build_row("damage", player, enemy))

    def auto_record(self, player, enemy):
        self.frame_timer += 1
        self.survival_time = self._survival_sec()
        if self.frame_timer >= 60:
            self.frame_timer = 0
            dist = math.hypot(player.pos[0] - enemy.pos[0], player.pos[1] - enemy.pos[1])
            row = self._build_row("position", player, enemy)
            self.log_buffer.append(row)
            if dist < 100:
                self.log_buffer.append(self._build_row("enemy_proximity", player, enemy))

    def log_game_over(self, player, enemy):
        self.log_buffer.append(self._build_row("game_over", player, enemy))
        self.save_to_csv()

    def save_to_csv(self):
        if not self.log_buffer:
            return
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerows(self.log_buffer)
        self.log_buffer.clear()