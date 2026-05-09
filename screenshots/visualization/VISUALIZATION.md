# Visualization Documentation

This folder contains screenshots of all data visualization components from the **Animal Escape — Statistics Viewer** (`stats_viewer.py`).

All data is collected automatically during gameplay and stored in `stats.csv`. The statistics viewer opens in a separate Tkinter window with three tabs: **All Graphs**, **Summary Stats**, and **Raw Data**.

---

## Overview Screenshot

**File:** `overview_all_graphs.png`

The "All Graphs" tab displays five charts arranged in a 2×3 grid, all rendered on a dark Catppuccin-inspired theme. At a glance, players can see item usage patterns, movement zones, mana management, combat damage history, and proximity to the enemy wolf.

---

## Component Screenshots

### 1. Item Collection Pie Chart

**File:** `item_collection.png`

This pie chart shows the proportion of each item type collected across all recorded sessions. Each slice corresponds to one item category (Heal, Shield, Clock, Wall, Trap, Star), with color coding matching the in-game item colors. This reveals which items players prioritize and rely on most.

**Key insight:** A dominance of Star items indicates a score-focused playstyle; a high proportion of Heal items suggests the player is frequently taking damage.

---

### 2. Player Position Zone Bar Chart

**File:** `bar_position_zone.png`

The maze is divided into four quadrants (Zone A: Top-Left, Zone B: Top-Right, Zone C: Bottom-Left, Zone D: Bottom-Right). This bar chart counts how often the player was recorded in each zone during `position` events (logged once per second). This identifies which areas of the map players favor or avoid.

**Key insight:** Uneven zone distribution can indicate that the wolf consistently pushes the player toward a corner, or that certain zones have a higher density of useful items.

---

### 3. Mana Usage Line Graph

**File:** `line_mana_usage.png`

This line graph plots the player's remaining mana over survival time (in seconds). Each data point corresponds to a `position` event. The filled area beneath the line makes drops in mana usage clearly visible. Mana is consumed when the player sprints (holds Left Shift) and regenerates slowly when not sprinting.

**Key insight:** Sharp drops followed by gradual recovery indicate sprint usage patterns. Consistently low mana may mean the player over-relies on sprinting, leaving them vulnerable when the wolf is nearby.

---

### 4. HP over Time Area Chart (Combat & Damage)

**File:** `hp_overtime.png`

This area chart plots the player's HP over survival time, combining `position`, `damage`, and `game_over` events for a complete picture. Purple scatter points mark exact moments when the wolf hit the player. The red filled area helps visualize the urgency of the player's health state throughout the session.

**Key insight:** Sudden drops in the area correspond to wolf attacks. If HP drops happen early and frequently, the player may not be using Shield or Heal items effectively.

---

### 5. Enemy Proximity Bar Chart

**File:** `bar_enemy_proximity.png`

This bar chart shows the average distance (in pixels) between the player and the wolf, grouped by character type, measured only when the wolf is within 100 pixels. This reveals whether different characters experience different risk levels due to their speed or player behavior differences.

**Key insight:** A lower average proximity for a character type means that character tends to get caught more often or plays more aggressively near the wolf.

---

### 6. Summary Statistics Table

**File:** `table_summary_stats.png`

This table (in the "Summary Stats" tab) presents Mean, Median, Max, and Min values for four key metrics across all recorded sessions: Survival Time, Remaining Mana, Enemy Distance, and Final Score. Additional session-level info (High score, total sessions, characters used, total items collected) appears below the table.

**Key insight:** Comparing Mean vs. Median survival time reveals whether a few very long sessions are skewing the average, or if most sessions end at a similar time.

---

### 7. Raw Data Table

**File:** `raw_data.png`

This table (in the "Raw Data" tab) displays the most recent 200 records loaded directly from `stats.csv`, shown in reverse chronological order so the latest events appear at the top. Each row represents one logged event and includes the following columns: `timestamp`, `event`, `char_type`, `score`, `hp`, `mana`, `player_x`, `player_y`, `enemy_dist`, `item_type`, and `survival_time`.

The table uses alternating row colors (dark grey / darker grey) for readability and supports vertical scrolling to browse all displayed records.

**Key insight:** The raw data tab is useful for verifying that the logger is recording events correctly — checking that `item_collect` rows contain the expected `item_type`, that `damage` events correspond to HP drops, and that `position` events are recorded at consistent time intervals throughout the session.

---