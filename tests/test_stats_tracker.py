"""
test_stats_tracker.py
Tests for game-logic data tracking: player stat calculations,
item score multipliers, wolf speed scaling, and CSV data integrity.
All tests run without pygame (pure-Python logic only).
"""

import csv
import math
import os
import tempfile
import unittest


# ── Minimal stubs ─────────────────────────────────────────────────────────

class FakePlayer:
    def __init__(self, char_type="Pig", hp=200, mana=50, score=0, pos=None,
                 max_hp=200, max_mana=50):
        self.char_type          = char_type
        self.hp                 = hp
        self.max_hp             = max_hp
        self.mana               = mana
        self.max_mana           = max_mana
        self.score              = score
        self.pos                = pos or [390.0, 270.0]
        self.is_shielded        = False
        self.speed_boost_timer  = 0
        self.wall_phase_timer   = 0
        self.is_wall_phasing    = False
        self.invulnerable_timer = 0
        self.pending_trap_timer = 0
        self.regen_timer        = 0
        self.base_speed         = 3
        self.speed              = 3
        self.water_slow_timer   = 0

    # --- Replicated logic from player.py (no pygame) ---

    def add_score(self, amount):
        if self.char_type == "Sheep":
            self.score += amount * 2
        else:
            self.score += amount

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

    def apply_water_effect(self):
        self.water_slow_timer = 30
        if self.invulnerable_timer <= 0:
            if self.is_shielded:
                self.is_shielded = False
            else:
                self.hp -= 10
            self.invulnerable_timer = 60


class FakeEnemy:
    def __init__(self, pos=None, base_speed=1.0):
        self.pos        = pos or [30.0, 30.0]
        self.base_speed = base_speed
        self.speed      = base_speed
        self.stun_timer = 0
        self.slow_timer = 0


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 1  — Player score & multiplier (8 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestPlayerScore(unittest.TestCase):

    def test_pig_score_normal(self):
        p = FakePlayer("Pig", score=0)
        p.add_score(5)
        self.assertEqual(p.score, 5)

    def test_rabbit_score_normal(self):
        p = FakePlayer("Rabbit", score=0)
        p.add_score(3)
        self.assertEqual(p.score, 3)

    def test_sheep_score_doubled(self):
        p = FakePlayer("Sheep", score=0)
        p.add_score(1)
        self.assertEqual(p.score, 2)

    def test_sheep_score_doubled_multiple(self):
        p = FakePlayer("Sheep", score=0)
        for _ in range(5):
            p.add_score(1)
        self.assertEqual(p.score, 10)

    def test_pig_score_accumulates(self):
        p = FakePlayer("Pig", score=10)
        p.add_score(5)
        self.assertEqual(p.score, 15)

    def test_sheep_multiplier_vs_pig(self):
        pig   = FakePlayer("Pig",   score=0)
        sheep = FakePlayer("Sheep", score=0)
        pig.add_score(4)
        sheep.add_score(4)
        self.assertEqual(sheep.score, pig.score * 2)

    def test_score_zero_add(self):
        p = FakePlayer("Pig", score=7)
        p.add_score(0)
        self.assertEqual(p.score, 7)

    def test_score_large_amount(self):
        p = FakePlayer("Sheep", score=0)
        p.add_score(100)
        self.assertEqual(p.score, 200)


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 2  — Player damage & invulnerability (8 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestPlayerDamage(unittest.TestCase):

    def test_take_damage_reduces_hp(self):
        p = FakePlayer(hp=200)
        p.take_damage(50)
        self.assertEqual(p.hp, 150)

    def test_take_damage_returns_true(self):
        p = FakePlayer(hp=200)
        result = p.take_damage(50)
        self.assertTrue(result)

    def test_invulnerable_blocks_second_hit(self):
        p = FakePlayer(hp=200)
        p.take_damage(50)
        result = p.take_damage(50)
        self.assertFalse(result)

    def test_hp_unchanged_during_invulnerability(self):
        p = FakePlayer(hp=200)
        p.take_damage(50)
        p.take_damage(50)    # blocked
        self.assertEqual(p.hp, 150)

    def test_invulnerable_timer_set_after_hit(self):
        p = FakePlayer(hp=200)
        p.take_damage(30)
        self.assertGreater(p.invulnerable_timer, 0)

    def test_damage_can_kill(self):
        p = FakePlayer(hp=50)
        p.take_damage(50)
        self.assertLessEqual(p.hp, 0)

    def test_partial_damage(self):
        p = FakePlayer(hp=100)
        p.take_damage(25)
        self.assertEqual(p.hp, 75)

    def test_shield_does_not_prevent_damage_logic(self):
        """take_damage itself doesn't check shield — shield handled externally."""
        p = FakePlayer(hp=200)
        p.is_shielded = True
        p.take_damage(50)
        self.assertEqual(p.hp, 150)


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 3  — Player use_item effects (8 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestPlayerUseItem(unittest.TestCase):

    def test_heal_increases_hp(self):
        p = FakePlayer(hp=180, max_hp=200)
        p.use_item("heal")
        self.assertEqual(p.hp, 200)

    def test_heal_capped_at_max(self):
        p = FakePlayer(hp=195, max_hp=200)
        p.use_item("heal")
        self.assertEqual(p.hp, 200)

    def test_heal_at_full_hp(self):
        p = FakePlayer(hp=200, max_hp=200)
        p.use_item("heal")
        self.assertEqual(p.hp, 200)

    def test_shield_activates(self):
        p = FakePlayer()
        p.use_item("shield")
        self.assertTrue(p.is_shielded)

    def test_clock_sets_speed_timer(self):
        p = FakePlayer()
        p.use_item("clock")
        self.assertEqual(p.speed_boost_timer, 120)

    def test_wall_sets_phase_flag(self):
        p = FakePlayer()
        p.use_item("wall")
        self.assertTrue(p.is_wall_phasing)

    def test_wall_sets_phase_timer(self):
        p = FakePlayer()
        p.use_item("wall")
        self.assertEqual(p.wall_phase_timer, 60)

    def test_unknown_item_no_error(self):
        p = FakePlayer()
        try:
            p.use_item("unknown_item")
        except Exception as e:
            self.fail(f"use_item raised for unknown item: {e}")


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 4  — Wolf speed scaling (7 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestWolfSpeedScaling(unittest.TestCase):
    """Wolf speed = base_speed + (score // 10) * 0.2 (from map_manager.py)."""

    def _wolf_speed(self, base, score):
        wolf = FakeEnemy(base_speed=base)
        wolf.speed = wolf.base_speed + (score // 10) * 0.2
        return wolf.speed

    def test_score_zero_no_bonus(self):
        self.assertAlmostEqual(self._wolf_speed(1.0, 0), 1.0)

    def test_score_10_one_bonus(self):
        self.assertAlmostEqual(self._wolf_speed(1.0, 10), 1.2)

    def test_score_20_two_bonuses(self):
        self.assertAlmostEqual(self._wolf_speed(1.0, 20), 1.4)

    def test_score_50_five_bonuses(self):
        self.assertAlmostEqual(self._wolf_speed(1.0, 50), 2.0)

    def test_score_9_no_bonus(self):
        self.assertAlmostEqual(self._wolf_speed(1.0, 9), 1.0)

    def test_speed_increases_with_score(self):
        s1 = self._wolf_speed(1.0, 10)
        s2 = self._wolf_speed(1.0, 30)
        self.assertGreater(s2, s1)

    def test_high_score_still_finite(self):
        speed = self._wolf_speed(1.0, 1000)
        self.assertTrue(math.isfinite(speed))


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 5  — Water trap effect (4 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestWaterTrap(unittest.TestCase):

    def test_water_sets_slow_timer(self):
        p = FakePlayer(hp=200)
        p.apply_water_effect()
        self.assertEqual(p.water_slow_timer, 30)

    def test_water_damages_unshielded(self):
        p = FakePlayer(hp=200)
        p.apply_water_effect()
        self.assertLess(p.hp, 200)

    def test_water_breaks_shield(self):
        p = FakePlayer(hp=200)
        p.is_shielded = True
        p.apply_water_effect()
        self.assertFalse(p.is_shielded)

    def test_water_no_damage_when_shielded(self):
        p = FakePlayer(hp=200)
        p.is_shielded = True
        p.apply_water_effect()
        self.assertEqual(p.hp, 200)


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 6  — CSV data integrity (10 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestCSVIntegrity(unittest.TestCase):
    """Write rows manually and verify structure/types."""

    FIELDNAMES = [
        "timestamp", "event", "char_type", "score", "hp", "mana",
        "player_x", "player_y", "enemy_x", "enemy_y", "enemy_dist",
        "item_type", "survival_time",
    ]

    def _make_row(self, **kwargs):
        base = {
            "timestamp": "1.0", "event": "position", "char_type": "Pig",
            "score": "0", "hp": "200", "mana": "50",
            "player_x": "390", "player_y": "270",
            "enemy_x": "30", "enemy_y": "30", "enemy_dist": "506.1",
            "item_type": "", "survival_time": "1.0",
        }
        base.update(kwargs)
        return base

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".csv")
        with open(self.tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            w.writeheader()

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def _write_rows(self, rows):
        with open(self.tmp, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            w.writerows(rows)

    def _read_rows(self):
        with open(self.tmp, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_header_present(self):
        rows = self._read_rows()
        self.assertEqual(rows, [])   # header only, no data rows

    def test_single_row_written(self):
        self._write_rows([self._make_row()])
        self.assertEqual(len(self._read_rows()), 1)

    def test_event_field_readable(self):
        self._write_rows([self._make_row(event="item_collect")])
        self.assertEqual(self._read_rows()[0]["event"], "item_collect")

    def test_score_is_numeric(self):
        self._write_rows([self._make_row(score="7")])
        self.assertEqual(int(self._read_rows()[0]["score"]), 7)

    def test_hp_is_numeric(self):
        self._write_rows([self._make_row(hp="150.5")])
        self.assertAlmostEqual(float(self._read_rows()[0]["hp"]), 150.5)

    def test_enemy_dist_non_negative(self):
        self._write_rows([self._make_row(enemy_dist="42.3")])
        self.assertGreaterEqual(float(self._read_rows()[0]["enemy_dist"]), 0)

    def test_multiple_rows_preserved(self):
        rows = [self._make_row(score=str(i)) for i in range(10)]
        self._write_rows(rows)
        self.assertEqual(len(self._read_rows()), 10)

    def test_item_type_field_exists(self):
        self._write_rows([self._make_row(item_type="heal")])
        self.assertEqual(self._read_rows()[0]["item_type"], "heal")

    def test_char_type_field_preserved(self):
        for char in ["Pig", "Rabbit", "Sheep"]:
            self._write_rows([self._make_row(char_type=char)])
        chars = [r["char_type"] for r in self._read_rows()]
        self.assertIn("Sheep", chars)

    def test_all_fieldnames_present_in_header(self):
        with open(self.tmp, newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))
        for fn in self.FIELDNAMES:
            self.assertIn(fn, header)


if __name__ == "__main__":
    unittest.main()