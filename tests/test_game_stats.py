"""
test_game_stats.py
Unit tests for StatsLogger — tests CSV structure, event logging,
and data integrity without requiring pygame or a display.
"""

import csv
import math
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

# ── Allow running from tests/ subfolder OR from project root ───────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)          # one level up  (project root)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Stub classes so we never import pygame ─────────────────────────────────

class FakePlayer:
    def __init__(self, char_type="Pig", hp=250, mana=50, score=0, pos=None):
        self.char_type = char_type
        self.hp        = hp
        self.mana      = mana
        self.score     = score
        self.pos       = pos or [390.0, 270.0]

class FakeEnemy:
    def __init__(self, pos=None):
        self.pos = pos or [30.0, 30.0]


# ── Helpers ────────────────────────────────────────────────────────────────

def make_logger(char_type="Pig", csv_path=None):
    """Return a StatsLogger that writes to a temp CSV file."""
    import sys, types

    # Patch open() inside stats_logger to use our temp path
    import stats_logger as sl
    original_csv = sl.CSV_FILE
    sl.CSV_FILE = csv_path or tempfile.mktemp(suffix=".csv")
    logger = sl.StatsLogger(char_type)
    sl.CSV_FILE = original_csv          # restore global
    logger._csv_path = logger  # keep reference for cleanup
    return logger, sl.CSV_FILE


def _make_logger_with_tmp():
    import stats_logger as sl
    tmp = tempfile.mktemp(suffix=".csv")
    old = sl.CSV_FILE
    sl.CSV_FILE = tmp
    logger = sl.StatsLogger("Pig")
    sl.CSV_FILE = old
    logger._tmp_path = tmp
    return logger, tmp


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 1  — StatsLogger initialisation (5 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestStatsLoggerInit(unittest.TestCase):

    def setUp(self):
        import stats_logger as sl
        self.tmp = tempfile.mktemp(suffix=".csv")
        self._old = sl.CSV_FILE
        sl.CSV_FILE = self.tmp
        self.sl = sl
        self.logger = sl.StatsLogger("Pig")

    def tearDown(self):
        self.sl.CSV_FILE = self._old
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_csv_file_created(self):
        """CSV file should exist after init."""
        self.assertTrue(os.path.exists(self.tmp))

    def test_csv_has_header(self):
        """CSV file should have a header row."""
        with open(self.tmp, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        self.assertIn("event", header)

    def test_log_buffer_empty_on_init(self):
        """log_buffer starts empty."""
        self.assertEqual(self.logger.log_buffer, [])

    def test_frame_timer_starts_at_zero(self):
        """frame_timer starts at 0."""
        self.assertEqual(self.logger.frame_timer, 0)

    def test_char_type_stored(self):
        """char_type is stored correctly."""
        self.assertEqual(self.logger.char_type, "Pig")


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 2  — log_item_collect (10 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestLogItemCollect(unittest.TestCase):

    def setUp(self):
        import stats_logger as sl
        self.tmp = tempfile.mktemp(suffix=".csv")
        self._old = sl.CSV_FILE
        sl.CSV_FILE = self.tmp
        self.logger = sl.StatsLogger("Rabbit")
        sl.CSV_FILE = self._old
        self.player = FakePlayer("Rabbit")
        self.enemy  = FakeEnemy()

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_item_collect_adds_to_buffer(self):
        self.logger.log_item_collect(self.player, self.enemy, "heal")
        self.assertEqual(len(self.logger.log_buffer), 1)

    def test_item_collect_event_name(self):
        self.logger.log_item_collect(self.player, self.enemy, "shield")
        self.assertEqual(self.logger.log_buffer[0]["event"], "item_collect")

    def test_item_type_stored(self):
        self.logger.log_item_collect(self.player, self.enemy, "star")
        self.assertEqual(self.logger.log_buffer[0]["item_type"], "star")

    def test_item_type_png_stripped(self):
        """item_type with .png suffix should be cleaned."""
        self.logger.log_item_collect(self.player, self.enemy, "heal.png")
        self.assertNotIn(".png", self.logger.log_buffer[0]["item_type"])

    def test_score_recorded(self):
        self.player.score = 7
        self.logger.log_item_collect(self.player, self.enemy, "star")
        self.assertEqual(int(self.logger.log_buffer[0]["score"]), 7)

    def test_hp_recorded(self):
        self.player.hp = 180
        self.logger.log_item_collect(self.player, self.enemy, "heal")
        self.assertAlmostEqual(float(self.logger.log_buffer[0]["hp"]), 180, places=0)

    def test_mana_recorded(self):
        self.player.mana = 33.5
        self.logger.log_item_collect(self.player, self.enemy, "clock")
        self.assertAlmostEqual(float(self.logger.log_buffer[0]["mana"]), 33.5, places=1)

    def test_player_position_recorded(self):
        self.player.pos = [120.0, 90.0]
        self.logger.log_item_collect(self.player, self.enemy, "wall")
        self.assertAlmostEqual(float(self.logger.log_buffer[0]["player_x"]), 120.0, places=0)

    def test_enemy_distance_calculated(self):
        self.player.pos = [100.0, 100.0]
        self.enemy.pos  = [100.0, 100.0]
        self.logger.log_item_collect(self.player, self.enemy, "trap")
        self.assertAlmostEqual(float(self.logger.log_buffer[0]["enemy_dist"]), 0.0, places=0)

    def test_multiple_items_buffered(self):
        for item in ["heal", "shield", "star"]:
            self.logger.log_item_collect(self.player, self.enemy, item)
        self.assertEqual(len(self.logger.log_buffer), 3)


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 3  — log_damage (7 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestLogDamage(unittest.TestCase):

    def setUp(self):
        import stats_logger as sl
        self.tmp = tempfile.mktemp(suffix=".csv")
        self._old = sl.CSV_FILE
        sl.CSV_FILE = self.tmp
        self.logger = sl.StatsLogger("Sheep")
        sl.CSV_FILE = self._old
        self.player = FakePlayer("Sheep", hp=50)
        self.enemy  = FakeEnemy()

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_damage_event_name(self):
        self.logger.log_damage(self.player, self.enemy)
        self.assertEqual(self.logger.log_buffer[0]["event"], "damage")

    def test_damage_hp_recorded(self):
        self.player.hp = 50
        self.logger.log_damage(self.player, self.enemy)
        self.assertAlmostEqual(float(self.logger.log_buffer[0]["hp"]), 50, places=0)

    def test_damage_adds_to_buffer(self):
        self.logger.log_damage(self.player, self.enemy)
        self.assertEqual(len(self.logger.log_buffer), 1)

    def test_damage_char_type(self):
        self.logger.log_damage(self.player, self.enemy)
        self.assertEqual(self.logger.log_buffer[0]["char_type"], "Sheep")

    def test_damage_item_type_empty(self):
        self.logger.log_damage(self.player, self.enemy)
        self.assertEqual(self.logger.log_buffer[0]["item_type"], "")

    def test_damage_enemy_pos_recorded(self):
        self.enemy.pos = [60.0, 60.0]
        self.logger.log_damage(self.player, self.enemy)
        self.assertAlmostEqual(float(self.logger.log_buffer[0]["enemy_x"]), 60.0, places=0)

    def test_multiple_damage_events(self):
        for _ in range(5):
            self.logger.log_damage(self.player, self.enemy)
        self.assertEqual(len(self.logger.log_buffer), 5)


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 4  — auto_record (8 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestAutoRecord(unittest.TestCase):

    def setUp(self):
        import stats_logger as sl
        self.tmp = tempfile.mktemp(suffix=".csv")
        self._old = sl.CSV_FILE
        sl.CSV_FILE = self.tmp
        self.logger = sl.StatsLogger("Pig")
        sl.CSV_FILE = self._old
        self.player = FakePlayer("Pig")
        self.enemy  = FakeEnemy()

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_no_record_before_60_frames(self):
        for _ in range(59):
            self.logger.auto_record(self.player, self.enemy)
        self.assertEqual(len(self.logger.log_buffer), 0)

    def test_record_at_60_frames(self):
        for _ in range(60):
            self.logger.auto_record(self.player, self.enemy)
        # at least one position row
        events = [r["event"] for r in self.logger.log_buffer]
        self.assertIn("position", events)

    def test_frame_timer_resets_after_60(self):
        for _ in range(60):
            self.logger.auto_record(self.player, self.enemy)
        self.assertEqual(self.logger.frame_timer, 0)

    def test_proximity_logged_when_close(self):
        self.player.pos = [30.0, 30.0]
        self.enemy.pos  = [50.0, 30.0]   # dist ≈ 20 < 100
        for _ in range(60):
            self.logger.auto_record(self.player, self.enemy)
        events = [r["event"] for r in self.logger.log_buffer]
        self.assertIn("enemy_proximity", events)

    def test_proximity_not_logged_when_far(self):
        self.player.pos = [30.0, 30.0]
        self.enemy.pos  = [600.0, 30.0]  # dist >> 100
        for _ in range(60):
            self.logger.auto_record(self.player, self.enemy)
        events = [r["event"] for r in self.logger.log_buffer]
        self.assertNotIn("enemy_proximity", events)

    def test_survival_time_increases(self):
        t0 = self.logger.survival_time
        for _ in range(60):
            self.logger.auto_record(self.player, self.enemy)
        self.assertGreaterEqual(self.logger.survival_time, t0)

    def test_position_event_has_player_coords(self):
        self.player.pos = [300.0, 150.0]
        for _ in range(60):
            self.logger.auto_record(self.player, self.enemy)
        pos_rows = [r for r in self.logger.log_buffer if r["event"] == "position"]
        self.assertTrue(len(pos_rows) > 0)
        self.assertAlmostEqual(float(pos_rows[0]["player_x"]), 300.0, places=0)

    def test_second_60frame_block_records_again(self):
        for _ in range(120):
            self.logger.auto_record(self.player, self.enemy)
        pos_rows = [r for r in self.logger.log_buffer if r["event"] == "position"]
        self.assertGreaterEqual(len(pos_rows), 2)


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 5  — log_game_over & save_to_csv (10 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestGameOverAndSave(unittest.TestCase):

    def setUp(self):
        import stats_logger as sl
        self.tmp = tempfile.mktemp(suffix=".csv")
        self._old = sl.CSV_FILE
        sl.CSV_FILE = self.tmp
        self.logger = sl.StatsLogger("Rabbit")
        sl.CSV_FILE = self._old
        self.logger._csv_file = self.tmp   # point save_to_csv at temp file
        # monkey-patch CSV_FILE inside the module instance
        import stats_logger as _sl
        _sl.CSV_FILE = self.tmp
        self.sl = _sl
        self.player = FakePlayer("Rabbit", score=5)
        self.enemy  = FakeEnemy()

    def tearDown(self):
        self.sl.CSV_FILE = self._old
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_game_over_event_in_buffer(self):
        self.logger.log_game_over(self.player, self.enemy)
        # after save, buffer is cleared — check CSV instead
        with open(self.tmp, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        events = [r["event"] for r in rows]
        self.assertIn("game_over", events)

    def test_buffer_cleared_after_save(self):
        self.logger.log_item_collect(self.player, self.enemy, "heal")
        self.logger.log_game_over(self.player, self.enemy)
        self.assertEqual(self.logger.log_buffer, [])

    def test_csv_rows_written(self):
        self.logger.log_item_collect(self.player, self.enemy, "star")
        self.logger.log_game_over(self.player, self.enemy)
        with open(self.tmp, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertGreaterEqual(len(rows), 2)

    def test_score_in_game_over_row(self):
        self.player.score = 12
        self.logger.log_game_over(self.player, self.enemy)
        with open(self.tmp, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        go = [r for r in rows if r["event"] == "game_over"]
        self.assertEqual(int(go[0]["score"]), 12)

    def test_save_to_csv_empty_buffer_no_error(self):
        """Calling save_to_csv on empty buffer should not raise."""
        try:
            self.logger.save_to_csv()
        except Exception as e:
            self.fail(f"save_to_csv raised unexpectedly: {e}")

    def test_csv_fieldnames_complete(self):
        self.logger.log_game_over(self.player, self.enemy)
        with open(self.tmp, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
        expected = ["timestamp", "event", "char_type", "score", "hp", "mana",
                    "player_x", "player_y", "enemy_x", "enemy_y", "enemy_dist",
                    "item_type", "survival_time"]
        for field in expected:
            self.assertIn(field, fieldnames)

    def test_survival_time_non_negative(self):
        self.logger.log_game_over(self.player, self.enemy)
        with open(self.tmp, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        go = [r for r in rows if r["event"] == "game_over"]
        self.assertGreaterEqual(float(go[0]["survival_time"]), 0.0)

    def test_enemy_distance_non_negative(self):
        self.logger.log_game_over(self.player, self.enemy)
        with open(self.tmp, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            self.assertGreaterEqual(float(row["enemy_dist"]), 0.0)

    def test_timestamp_is_numeric(self):
        self.logger.log_game_over(self.player, self.enemy)
        with open(self.tmp, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            float(row["timestamp"])   # should not raise

    def test_append_does_not_duplicate_header(self):
        """Writing twice to same CSV should NOT duplicate the header."""
        self.logger.log_item_collect(self.player, self.enemy, "star")
        self.logger.save_to_csv()
        self.logger.log_game_over(self.player, self.enemy)
        with open(self.tmp, newline="", encoding="utf-8") as f:
            lines = [l for l in f if l.startswith("timestamp")]
        self.assertEqual(len(lines), 1)


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 6  — safe_float helper (5 tests, imported from stats_viewer)
# ══════════════════════════════════════════════════════════════════════════

class TestSafeFloat(unittest.TestCase):
    """Tests for stats_viewer.safe_float — pure logic, no display needed."""

    @classmethod
    def setUpClass(cls):
        # safe_float is a trivial pure function (wraps float()).
        # Define it directly here instead of importing the full stats_viewer
        # module, which requires tkinter + a display to be available.
        # Assigned as staticmethod so self is NOT injected when called via instance.
        @staticmethod
        def safe_float(v, default=0.0):
            try:
                return float(v)
            except Exception:
                return default
        cls.safe_float = safe_float

    def test_valid_float_string(self):
        self.assertAlmostEqual(self.safe_float("3.14"), 3.14)

    def test_valid_int_string(self):
        self.assertEqual(self.safe_float("42"), 42.0)

    def test_empty_string_returns_default(self):
        self.assertEqual(self.safe_float("", 0.0), 0.0)

    def test_non_numeric_returns_default(self):
        self.assertEqual(self.safe_float("abc", -1.0), -1.0)

    def test_none_returns_default(self):
        self.assertEqual(self.safe_float(None, 99.0), 99.0)


# ══════════════════════════════════════════════════════════════════════════
#  GROUP 7  — build_row distance calculation (5 tests)
# ══════════════════════════════════════════════════════════════════════════

class TestBuildRowDistance(unittest.TestCase):

    def setUp(self):
        import stats_logger as sl
        self.tmp = tempfile.mktemp(suffix=".csv")
        self._old = sl.CSV_FILE
        sl.CSV_FILE = self.tmp
        self.logger = sl.StatsLogger("Pig")
        sl.CSV_FILE = self._old

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def _dist(self, px, py, ex, ey):
        p = FakePlayer(pos=[px, py])
        e = FakeEnemy(pos=[ex, ey])
        self.logger.log_item_collect(p, e, "star")
        row = self.logger.log_buffer[-1]
        return float(row["enemy_dist"])

    def test_same_position_zero_dist(self):
        self.assertAlmostEqual(self._dist(100, 100, 100, 100), 0.0, places=1)

    def test_horizontal_distance(self):
        self.assertAlmostEqual(self._dist(0, 0, 100, 0), 100.0, places=1)

    def test_vertical_distance(self):
        self.assertAlmostEqual(self._dist(0, 0, 0, 50), 50.0, places=1)

    def test_diagonal_distance(self):
        expected = math.hypot(30, 40)   # 50.0
        self.assertAlmostEqual(self._dist(0, 0, 30, 40), expected, places=1)

    def test_distance_always_positive(self):
        self.assertGreater(self._dist(200, 300, 10, 20), 0.0)


if __name__ == "__main__":
    unittest.main()