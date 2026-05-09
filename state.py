"""
Stack Attack Reborn — Shared Mutable Game State

Central store for all runtime state that multiple modules need to read/write.
This avoids circular imports while keeping globals explicit and contained.
"""
from constants import COLS, ROWS, INITIAL_SPAWN_MS

# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------
board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
helmet_timers = [[0 for _ in range(COLS)] for _ in range(ROWS)]
bomb_timers = [[0 for _ in range(COLS)] for _ in range(ROWS)]

# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
player = None

# ---------------------------------------------------------------------------
# Falling crates & push animations
# ---------------------------------------------------------------------------
falling_boxes = []
push_animations = []

# ---------------------------------------------------------------------------
# Scoring & difficulty
# ---------------------------------------------------------------------------
score = 0
difficulty = 1.0
spawn_interval = INITIAL_SPAWN_MS
combo_count = 0

# ---------------------------------------------------------------------------
# Visual effects
# ---------------------------------------------------------------------------
screen_shake = 0
particles = []
explosion_anim_cells = []
explosion_anim_timer = 0
floating_explosions = []
line_clear_flash = 0
match_anim_cells = []
match_anim_timer = 0

# ---------------------------------------------------------------------------
# Crane
# ---------------------------------------------------------------------------
cranes = []
crane_frame = 0

# ---------------------------------------------------------------------------
# UI / Menu
# ---------------------------------------------------------------------------
game_state = "title"
selected_char = 0
selected_level = 1

# ---------------------------------------------------------------------------
# Character Specifics
# ---------------------------------------------------------------------------
pete_temp_ability = None
pete_ability_timer = 0

