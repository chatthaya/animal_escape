# Animal Escape — Maze Survival

## Project Description

- **Project by:** Chatthaya Tipatnaranan 6810545531
- **Game Genre:** Action, Survival, Maze

Animal Escape is a 2D top-down maze survival game built with Python and Pygame. The player controls an animal character trying to survive as long as possible while being chased by an AI-controlled wolf. Players collect items scattered throughout the maze to boost their stats, slow the enemy, or score points.

---

## Installation

To clone this project:

```sh
git clone https://github.com/chatthaya/animal_escape.git
cd animal_escape
```

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Mac / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running Guide

After activating the Python environment, run the game with:

### Windows

```bat
python main.py
```

### Mac / Linux

```sh
python3 main.py
```

To view statistics separately (without launching the game):

```sh
python stats_viewer.py   # Windows: python stats_viewer.py
```

---

## Tutorial / Usage

### Main Menu
| Button | Action |
|---|---|
| **PLAY** | Go to character selection |
| **STATISTICS** | Open the statistics viewer window |
| **EXIT** | Quit the game |

### Character Selection
Pick one of three animals, then press **START!**

| Character | HP | Mana | Special |
|---|---|---|---|
| Pig | 250 | 50 | Tanky |
| Rabbit | 200 | 75 | High mana |
| Sheep | 100 | 25 | x2 item score |

### In-Game Controls

| Key | Action |
|---|---|
| `W / ↑` | Move Up |
| `S / ↓` | Move Down |
| `A / ←` | Move Left |
| `D / →` | Move Right |
| `Left Shift` (hold) | Sprint (uses Mana) |
| `Esc` | Pause / Resume |

### Items

| Item | Effect |
|---|---|
| ❤️ Heal | Restores 20 HP |
| 🛡️ Shield | Blocks one hit from the wolf |
| ⏰ Clock | Speed boost for 2 seconds |
| 🧱 Wall | Walk through walls for 1 second |
| 🪤 Trap | Places a trap that slows the wolf |
| ⭐ Star | +1 Score (×2 for Sheep) |

---

## Game Features

- **A* Pathfinding** — The wolf uses A* to intelligently navigate the maze toward the player
- **3 Playable Characters** — Each with unique HP, Mana, and a special ability
- **6 Item Types** — Collectible power-ups that respawn every 2 seconds
- **Water Traps** — Randomly placed hazards that slow and damage the player
- **Wall Phase** — Temporarily pass through walls
- **Dynamic Difficulty** — Wolf speed increases as the player's score grows
- **Pause Menu** — Pause, return to menu, or exit mid-game
- **Statistics Tracking** — All game events are logged to `stats.csv` and visualized

---

## Known Bugs

- Wall-phase exit may rarely place the player slightly off-center if the nearest open tile is far away

---

## Unfinished Works

All planned features within the defined project scope have been fully implemented, including:
- A* pathfinding wolf AI
- 3 playable characters with unique stats
- 6 collectible item types with distinct effects
- Water trap environmental hazards
- Dynamic difficulty scaling (wolf speed)
- CSV-based statistics logging
- Statistics viewer with 5 graphs and a summary table

Features listed in the original proposal but intentionally revised during development are documented in [`DESCRIPTION.md` — Section 6: Changed Proposed Features](./DESCRIPTION.md).

---

## External Sources

Acknowledge to:

1. A* Pathfinding algorithm — adapted from standard heapq-based implementation
2. Pygame documentation — https://www.pygame.org/docs/
3. Matplotlib documentation — https://matplotlib.org/stable/
4. Character and item artwork — Original artwork and curated assets from Pinterest.