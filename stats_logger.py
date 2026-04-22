import csv
import os
import time
import math

CSV_FILE = "stats.csv"

# หัวคอลัมน์ของไฟล์ CSV
FIELDNAMES = [
    "timestamp",        # เวลาที่บันทึก (วินาทีในเกม)
    "event",            # ประเภทเหตุการณ์: item_collect, damage, position, game_over
    "char_type",        # ตัวละครที่เลือก
    "score",            # คะแนนขณะนั้น
    "hp",               # HP ขณะนั้น
    "mana",             # Mana ขณะนั้น
    "player_x",         # ตำแหน่ง X ของผู้เล่น
    "player_y",         # ตำแหน่ง Y ของผู้เล่น
    "enemy_x",          # ตำแหน่ง X ของศัตรู
    "enemy_y",          # ตำแหน่ง Y ของศัตรู
    "enemy_dist",       # ระยะห่างระหว่างผู้เล่นและศัตรู
    "item_type",        # ชนิดไอเทมที่เก็บ (ถ้ามี)
    "survival_time",    # เวลารอดชีวิต (วินาที)
]


class StatsLogger:
    def __init__(self, char_type):
        self.char_type = char_type
        self.log_buffer = []
        self.start_time = time.time()
        self.frame_timer = 0          # นับเฟรมสำหรับบันทึกทุก 60 เฟรม (1 วินาที)
        self.survival_time = 0.0

        # สร้างไฟล์ถ้ายังไม่มี / เขียนหัวคอลัมน์ถ้าไฟล์ว่าง
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

    # ---- Public API ----

    def log_item_collect(self, player, enemy, item_type):
        """เรียกทุกครั้งที่ผู้เล่นเก็บไอเทม"""
        clean_type = str(item_type).replace(".png", "")
        self.log_buffer.append(self._build_row("item_collect", player, enemy, clean_type))

    def log_damage(self, player, enemy):
        """เรียกทุกครั้งที่ผู้เล่นโดนดาเมจ"""
        self.log_buffer.append(self._build_row("damage", player, enemy))

    def auto_record(self, player, enemy):
        """เรียกทุกเฟรม — บันทึก position + mana ทุก 60 เฟรม (≈1 วินาที)"""
        self.frame_timer += 1
        self.survival_time = self._survival_sec()
        if self.frame_timer >= 60:
            self.frame_timer = 0
            dist = math.hypot(player.pos[0] - enemy.pos[0], player.pos[1] - enemy.pos[1])
            row = self._build_row("position", player, enemy)
            self.log_buffer.append(row)
            # บันทึกระยะศัตรูเฉพาะเมื่ออยู่ใกล้ (< 100 px)
            if dist < 100:
                self.log_buffer.append(self._build_row("enemy_proximity", player, enemy))

    def log_game_over(self, player, enemy):
        """เรียกเมื่อเกมจบ"""
        self.log_buffer.append(self._build_row("game_over", player, enemy))
        self.save_to_csv()

    def save_to_csv(self):
        """Flush buffer ทั้งหมดลง CSV"""
        if not self.log_buffer:
            return
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerows(self.log_buffer)
        self.log_buffer.clear()