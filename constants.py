"""
Stack Attack Reborn — Game Constants & Configuration

All magic numbers, tile sizes, colors, frame mappings, and tuning values
live here so every other module can import them without circular deps.
"""
import os
import pygame

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")
HIGHSCORES_FILE = os.path.join(BASE_DIR, "highscores.json")

# ---------------------------------------------------------------------------
# Grid & Display
# ---------------------------------------------------------------------------
TILE_SIZE = 40
COLS = 12
ROWS = 12
WIDTH = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE
HUD_H = 60
CONTROLS_H = 200

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
MAGENTA = (255, 0, 255)

# ---------------------------------------------------------------------------
# Crate Types
# ---------------------------------------------------------------------------
NUM_CRATE_TYPES = 5
BOMB_TYPE = 8
SAM_BOMB_TYPE = 9
POWERUP_HELMET_TYPE = 6

# ---------------------------------------------------------------------------
# Timing (ms)
# ---------------------------------------------------------------------------
GRAVITY_MS = 300
INITIAL_SPAWN_MS = 3000

# ---------------------------------------------------------------------------
# Pygame Custom Events
# ---------------------------------------------------------------------------
GRAVITY_EVENT = pygame.USEREVENT + 1
SPAWN_EVENT = pygame.USEREVENT + 2

# ---------------------------------------------------------------------------
# Animation Frame Indices
# ---------------------------------------------------------------------------
IDLE_FRAMES = [0, 1, 2, 3, 4, 5]
WALK_RIGHT_FRAMES = [6, 7, 8]
WALK_LEFT_FRAMES = [9, 10, 11]
PUSH_RIGHT_FRAMES = [12, 13, 14]
PUSH_LEFT_FRAMES = [15, 16, 17]
JUMP_RIGHT_FRAME = 18
JUMP_LEFT_FRAME = 19
STUN_FRAMES = [21, 22, 23, 24, 25, 26]
STUN_FRAME = 20 # Keep for single-frame references if any

# ---------------------------------------------------------------------------
# Physics & Gameplay Tuning
# ---------------------------------------------------------------------------
PUSH_SLIDE_SPEED = 2.5
JUMP_BUFFER_FRAMES = 8
COYOTE_FRAMES = 6
PUSH_HORIZONTAL_SPEED = 2.5

# ---------------------------------------------------------------------------
# Crane
# ---------------------------------------------------------------------------
CRANE_SPEED = 2.0
CRANE_COUNT = 5
CRANE_SPACING = int(TILE_SIZE * 2.5)
CRANE_Y = 0
CRANE_FW = 16  # frame width in the sprite sheet
CRANE_EMPTY_FRAME = 10
CRANE_FRAME_FOR_CRATE = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}

# ---------------------------------------------------------------------------
# Character Definitions
# ---------------------------------------------------------------------------
CHAR_DEFS = [
    {"id": "pete", "name": "Part-time Pete", "sprite": "man.png", "icon": "iconman.png",
     "speed": 3.5, "jump": -7.5, "super_jumps": 0, "bombs": 0, "ability": "promotion",
     "desc": "Promocao de Cargo. Ganha habilidade aleatoria por 10s ao fazer combo."},
    {"id": "lizzie", "name": "Lazy Lizzie", "sprite": "woman.png", "icon": "icwoman.png",
     "speed": 5.0, "jump": -7.5, "super_jumps": 0, "bombs": 0, "ability": "speed",
     "desc": "Veloz. A mais rapida do elenco."},
    {"id": "frank", "name": "Forklift Frank", "sprite": "man2.png", "icon": "iconman2.png",
     "speed": 4.0, "jump": -7.5, "super_jumps": 0, "bombs": 0, "ability": "double_push",
     "desc": "Empurrao Duplo. Empurra ate 2 caixas alinhadas de uma vez."},
    {"id": "will", "name": "Warehouse Will", "sprite": "man3.png", "icon": "iconman3.png",
     "speed": 4.0, "jump": -9.5, "super_jumps": 0, "bombs": 0, "ability": "high_jump",
     "desc": "Pulo Alto. Alcanca a altura de 2 caixas empilhadas."},
    {"id": "cath", "name": "Crate-Crazy Cath", "sprite": "woman2.png", "icon": "icwoman2.png",
     "speed": 4.0, "jump": -7.5, "super_jumps": 0, "bombs": 0, "ability": "color_clear",
     "desc": "Sobrecarga. Ao fazer um combo, destroi todas as caixas da mesma cor."},
    {"id": "sam", "name": "Super-Stacker Sam", "sprite": "man4.png", "icon": "iconman4.png",
     "speed": 4.5, "jump": -7.5, "super_jumps": 0, "bombs": 3, "ability": "bombs",
     "desc": "Demolidor. Tem bombas com raio 1 e recupera 1 ao combinar 3 cores.",
     "radius": 1}
]

# ---------------------------------------------------------------------------
# Dynamic Music
# ---------------------------------------------------------------------------
GAMEPLAY_MUSIC_FILES = [
    "gameplay_1.mid",  # 100 BPM - Relaxed
    "gameplay_2.mid",  # 120 BPM - Getting warmer
    "gameplay_3.mid",  # 140 BPM - Medium
    "gameplay_4.mid",  # 165 BPM - Intense
    "gameplay_5.mid",  # 195 BPM - Maximum chaos
]
MUSIC_THRESHOLDS = [1.0, 5.0, 10.0, 15.0, 20.0]
