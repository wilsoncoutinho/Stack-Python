import pygame
import sys
import random
import os
import json
import math

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    SOUND_OK = True
except Exception:
    SOUND_OK = False

TILE_SIZE, COLS, ROWS = 40, 12, 12
WIDTH = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE
HUD_H = 48
screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD_H))
pygame.display.set_caption("Stack Attack")
clock = pygame.time.Clock()
# Use modern and arcade fonts (Impact/Arial Black for that mobile look)
# The custom Jetpack Joyride Revived font only has glyphs for A-Z, a-z, 0-9, '.' and '$'.
# All other special characters (!, +, ,, :, ;, -, etc.) render as tofu squares.
# HybridFont renders each character with the correct font, using a system fallback
# for unsupported glyphs to maintain visual consistency.

# Characters that the custom font supports (verified visually)
_CUSTOM_FONT_CHARS = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.$"
)

def _get_fallback_font(size):
    """Get a system font as fallback for special characters."""
    for name in ["Impact", "Arial Black", "Segoe UI", "Verdana"]:
        try:
            f = pygame.font.SysFont(name, size, bold=True)
            if f:
                return f
        except Exception:
            continue
    return pygame.font.SysFont(None, size)


class HybridFont:
    """Renders text using a custom font for supported glyphs and a system
    fallback font for special characters that would otherwise be tofu."""

    def __init__(self, custom_font, fallback_font, size):
        self.custom = custom_font
        self.fallback = fallback_font
        self._size = size
        # Cache for the rendered character surfaces
        self._char_cache = {}

    def _font_for_char(self, ch):
        """Return the correct font for a given character."""
        if ch in _CUSTOM_FONT_CHARS or ch == ' ':
            return self.custom
        return self.fallback

    def render(self, text, antialias, color, background=None):
        """Render text, switching fonts per-character for unsupported glyphs."""
        # Fast path: if all chars are supported by the custom font, use it directly
        if all(c in _CUSTOM_FONT_CHARS or c == ' ' for c in text):
            if background:
                return self.custom.render(text, antialias, color, background)
            return self.custom.render(text, antialias, color)

        # Slow path: composite character by character
        # First, measure the total width and max height
        char_surfs = []
        total_w = 0
        max_h = 0
        for ch in text:
            font = self._font_for_char(ch)
            if background:
                s = font.render(ch, antialias, color, background)
            else:
                s = font.render(ch, antialias, color)
            char_surfs.append(s)
            total_w += s.get_width()
            max_h = max(max_h, s.get_height())

        # Composite onto a single surface
        if background:
            result = pygame.Surface((total_w, max_h))
            result.fill(background)
        else:
            result = pygame.Surface((total_w, max_h), pygame.SRCALPHA)

        x = 0
        for s in char_surfs:
            # Vertically center each character
            y_off = max_h - s.get_height()
            result.blit(s, (x, y_off))
            x += s.get_width()

        return result

    def size(self, text):
        """Return the (width, height) of the rendered text."""
        if all(c in _CUSTOM_FONT_CHARS or c == ' ' for c in text):
            return self.custom.size(text)
        w = 0
        h = 0
        for ch in text:
            font = self._font_for_char(ch)
            cw, ch2 = font.size(ch)
            w += cw
            h = max(h, ch2)
        return (w, h)

    def metrics(self, text):
        """Return per-character metrics."""
        result = []
        for ch in text:
            font = self._font_for_char(ch)
            m = font.metrics(ch)
            result.extend(m if m else [None])
        return result

    def get_height(self):
        return self.custom.get_height()

    def get_linesize(self):
        return self.custom.get_linesize()

    def get_ascent(self):
        return self.custom.get_ascent()

    def get_descent(self):
        return self.custom.get_descent()


def get_best_font(size, bold=True):
    # Support for the specific font provided in assets
    custom_path = os.path.join(ASSETS, "jetpack-joyride-revived.ttf", "jetpack-joyride-revived.ttf")
    if os.path.exists(custom_path):
        try:
            custom = pygame.font.Font(custom_path, size)
            fallback = _get_fallback_font(size)
            return HybridFont(custom, fallback, size)
        except Exception:
            pass

    preferred = ["Jetpack Joyride Revived", "Jetpack Joyride", "Impact", "Arial Black", "Segoe UI", "Inter", "Rubik", "Outfit", "Verdana"]
    for f in preferred:
        try:
            return pygame.font.SysFont(f, size, bold=bold)
        except Exception:
            continue
    return pygame.font.SysFont(None, size)

# Custom font metrics are much larger than system fonts, so we reduce base sizes significantly
font_big = get_best_font(20)
font_med = get_best_font(16)
font_sm = get_best_font(10)
font_xs = get_best_font(8)

def render_styled_text(text, font, color, outline_color=(0, 0, 0), outline_width=2, gradient=None):
    """Renders text with a thick outline and optional top-down gradient"""
    base = font.render(text, True, color)
    w, h = base.get_size()
    surf = pygame.Surface((w + outline_width*2, h + outline_width*2), pygame.SRCALPHA)
    
    # Draw thick outline (stamped)
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx*dx + dy*dy <= outline_width*outline_width:
                # Add a bit of shadow offset for a 3D feel
                out = font.render(text, True, outline_color)
                surf.blit(out, (outline_width + dx, outline_width + dy))
    
    # Extra drop shadow for "pop"
    shadow = font.render(text, True, (20, 20, 30))
    surf.blit(shadow, (outline_width + 2, outline_width + 2))

    if gradient:
        # Apply gradient to the core text
        grad_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        c1, c2 = gradient
        for y in range(h):
            r = c1[0] + (c2[0] - c1[0]) * y / h
            g = c1[1] + (c2[1] - c1[1]) * y / h
            b = c1[2] + (c2[2] - c1[2]) * y / h
            pygame.draw.line(grad_surf, (int(r), int(g), int(b), 255), (0, y), (w, y))
        
        mask = font.render(text, True, (255, 255, 255))
        grad_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(grad_surf, (outline_width, outline_width))
    else:
        surf.blit(base, (outline_width, outline_width))
    return surf

MAGENTA = (255, 0, 255)
NUM_CRATE_TYPES = 5
BOMB_TYPE = 8
POWERUP_HELMET_TYPE = 6
GRAVITY_MS = 300
INITIAL_SPAWN_MS = 3000
GRAVITY_EVENT = pygame.USEREVENT + 1
SPAWN_EVENT = pygame.USEREVENT + 2


def load_img(rel_path, colorkey=MAGENTA):
    path = os.path.join(ASSETS, rel_path)
    img = pygame.image.load(path).convert()
    img.set_colorkey(colorkey)
    return img


def slice_sheet(sheet, fw, fh, scale=1.0, count=None):
    frames = []
    limit = count if count else (sheet.get_width() // fw)
    for i in range(limit):
        sub = sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh))
        w = max(1, int(fw * scale))
        h = max(1, int(fh * scale))
        frames.append(pygame.transform.scale(sub, (w, h)))
    return frames


bg_img = pygame.transform.scale(load_img("extracted/back.png"), (WIDTH, HEIGHT))
title_img = pygame.transform.scale(load_img("extracted/title.png"), (WIDTH, HEIGHT + HUD_H))

crate_sprites = slice_sheet(load_img("extracted/crates.png"), 8, 8, TILE_SIZE / 8, count=14)
# Authentic bomb crate (saved to file for easy editing)
try:
    bomb_sprite = pygame.image.load(os.path.join(ASSETS, "extracted/crate_bomb.png")).convert_alpha()
except:
    # Fallback to procedural if file is missing
    bomb_sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
    bomb_sprite.fill((30, 30, 30))
    pygame.draw.rect(bomb_sprite, (0, 0, 0), (0, 0, TILE_SIZE, TILE_SIZE), 3)
    pygame.draw.rect(bomb_sprite, (220, 40, 40), (10, 10, 20, 20))

explosion_anim_cells = []
floating_explosions = []
explosion_anim_timer = 0
bomb_timers = [[0 for _ in range(COLS)] for _ in range(ROWS)]

screen_shake = 0
particles = []

def add_particles(x, y, color, count=10):
    for _ in range(count):
        particles.append({
            "x": x + random.randint(0, TILE_SIZE),
            "y": y + random.randint(0, TILE_SIZE),
            "vx": random.uniform(-3, 3),
            "vy": random.uniform(-5, -1),
            "life": random.randint(20, 40),
            "color": color
        })

def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.2 # Gravity
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)

# Crane sprites: full 16x18 frames (mechanism + crate built-in), scaled uniformly
CRANE_FW = 16  # actual frame width in the sprite sheet
crane_sprites = slice_sheet(load_img("extracted/crane.png"), CRANE_FW, 18, TILE_SIZE / 8)
# Frame mapping: crane frame index for each crate type (1-5) and empty
# Frame 0=yellow, 1=red, 2=green-striped, 3=blue, 4=red-variant, ..., 10=empty
CRANE_EMPTY_FRAME = 10
CRANE_FRAME_FOR_CRATE = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}  # crate_type -> crane frame
CRANE_SPRITE_W = crane_sprites[0].get_width() if crane_sprites else TILE_SIZE * 2
CRANE_SPRITE_H = crane_sprites[0].get_height() if crane_sprites else TILE_SIZE * 2

CHAR_DEFS = [
    {"id": "pete", "name": "Part-time Pete", "sprite": "man.png", "icon": "iconman.png",
     "speed": 3.5, "jump": -7.5, "super_jump": -10.5, "super_jumps": 0, "bombs": 0,
     "desc": "Basico. Sem super pulos."},
    {"id": "lizzie", "name": "Lazy Lizzie", "sprite": "woman.png", "icon": "icwoman.png",
     "speed": 4.5, "jump": -7.0, "super_jump": -11.5, "super_jumps": 4, "bombs": 0,
     "desc": "Rapida. 4 super pulos."},
    {"id": "frank", "name": "Forklift Frank", "sprite": "man2.png", "icon": "iconman2.png",
     "speed": 4.5, "jump": -8.0, "super_jump": -12.0, "super_jumps": 1, "bombs": 0,
     "desc": "Rapido, 1 super pulo."},
    {"id": "will", "name": "Warehouse Will", "sprite": "man3.png", "icon": "iconman3.png",
     "speed": 4.0, "jump": -7.5, "super_jump": -11.5, "super_jumps": 2, "bombs": 0,
     "desc": "Agil. 2 super pulos."},
    {"id": "cath", "name": "Crate-Crazy Cath", "sprite": "woman2.png", "icon": "icwoman2.png",
     "speed": 5.0, "jump": -7.5, "super_jump": -12.0, "super_jumps": 3, "bombs": 0,
     "desc": "Muito rapida. 3 super pulos."},
    {"id": "sam", "name": "Super-Stacker Sam", "sprite": "man4.png", "icon": "iconman4.png",
     "speed": 5.0, "jump": -8.0, "super_jump": -13.0, "super_jumps": 5, "bombs": 3,
     "desc": "O melhor! 5 super pulos + 3 bombas."},
]

char_sprites = {}
char_icons = {}
IDLE_FRAMES = [0, 1, 2, 3, 4, 5]
WALK_RIGHT_FRAMES = [6, 7, 8]
WALK_LEFT_FRAMES = [9, 10, 11]
PUSH_RIGHT_FRAMES = [12, 13, 14]
PUSH_LEFT_FRAMES = [15, 16, 17]
JUMP_RIGHT_FRAME = 18
JUMP_LEFT_FRAME = 19
STUN_FRAME = 20
PUSH_SLIDE_SPEED = 2.5
JUMP_BUFFER_FRAMES = 8
COYOTE_FRAMES = 6
PUSH_HORIZONTAL_SPEED = 2.5
CRANE_SPEED = 2.0
CRANE_COUNT = 5
CRANE_SPACING = int(TILE_SIZE * 2.5)              # spacing between cranes
CRANE_Y = 0                                        # Crane drawn at top of screen

for cdef in CHAR_DEFS:
    sheet = load_img("StackAttack2/" + cdef["sprite"])
    frames = slice_sheet(sheet, 8, 16, TILE_SIZE / 8)
    char_sprites[cdef["id"]] = frames
    icon_raw = load_img("StackAttack2/" + cdef["icon"])
    char_icons[cdef["id"]] = pygame.transform.scale(icon_raw, (TILE_SIZE, TILE_SIZE * 2))


def play_music(name, loops=0):
    if not SOUND_OK:
        return
    path = os.path.join(ASSETS, name)
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops)
        except Exception:
            pass


def stop_music():
    if SOUND_OK:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

def pause_music():
    if SOUND_OK:
        try:
            pygame.mixer.music.pause()
        except Exception:
            pass

def unpause_music():
    if SOUND_OK:
        try:
            pygame.mixer.music.unpause()
        except Exception:
            pass


# Dynamic gameplay music system
# 5 tempo levels that increase with difficulty
GAMEPLAY_MUSIC_FILES = [
    "gameplay_1.mid",  # 100 BPM - Relaxed
    "gameplay_2.mid",  # 120 BPM - Getting warmer
    "gameplay_3.mid",  # 140 BPM - Medium
    "gameplay_4.mid",  # 165 BPM - Intense
    "gameplay_5.mid",  # 195 BPM - Maximum chaos
]
# Difficulty thresholds for each music level
MUSIC_THRESHOLDS = [1.0, 2.0, 3.5, 5.5, 8.0]
current_music_level = 0
gameplay_music_playing = False


def get_music_level_for_difficulty(diff):
    """Returns the music level (0-4) for a given difficulty value."""
    level = 0
    for i, threshold in enumerate(MUSIC_THRESHOLDS):
        if diff >= threshold:
            level = i
    return level


def start_gameplay_music():
    """Start gameplay music at the appropriate tempo for current difficulty."""
    global current_music_level, gameplay_music_playing
    current_music_level = get_music_level_for_difficulty(difficulty)
    play_music(GAMEPLAY_MUSIC_FILES[current_music_level], loops=-1)
    gameplay_music_playing = True


def update_gameplay_music():
    """Check if difficulty warrants a tempo change and switch tracks."""
    global current_music_level, gameplay_music_playing
    if not gameplay_music_playing:
        return
    new_level = get_music_level_for_difficulty(difficulty)
    if new_level != current_music_level:
        current_music_level = new_level
        play_music(GAMEPLAY_MUSIC_FILES[current_music_level], loops=-1)


def stop_gameplay_music():
    """Stop gameplay music tracking."""
    global gameplay_music_playing
    gameplay_music_playing = False
    stop_music()


def load_sound(filename):
    """Load a sound effect and return the Sound object"""
    if not SOUND_OK:
        return None
    path = os.path.join(ASSETS, filename)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            pass
    return None


def play_sound(sound):
    """Play a sound effect if it's loaded"""
    if sound and SOUND_OK:
        try:
            sound.play()
        except Exception:
            pass


# Load sound effects (procedurally generated WAV files)
sound_jump = load_sound("sounds/jump.wav")
sound_super_jump = load_sound("sounds/super_jump.wav")
sound_push = load_sound("sounds/push.wav")
sound_land = load_sound("sounds/land.wav")
sound_explode = load_sound("sounds/explode.wav")
sound_powerup = load_sound("sounds/powerup.wav")
sound_bomb = load_sound("sounds/bomb.wav")
sound_stun = load_sound("sounds/stun.wav")
sound_combo = load_sound("sounds/combo.wav")
sound_line_clear = load_sound("sounds/line_clear.wav")
sound_game_over_sfx = load_sound("sounds/game_over.wav")
sound_menu_move = load_sound("sounds/menu_move.wav")
sound_menu_select = load_sound("sounds/menu_select.wav")
sound_helmet = load_sound("sounds/helmet.wav")


HIGHSCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscores.json")

def load_highscores():
    if os.path.exists(HIGHSCORES_FILE):
        try:
            with open(HIGHSCORES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_highscores(scores):
    try:
        with open(HIGHSCORES_FILE, "w") as f:
            json.dump(scores, f)
    except Exception:
        pass

highscores = load_highscores()


def approach(a, b, speed):
    diff = b - a
    if abs(diff) <= speed:
        return b
    return a + speed * (1 if diff > 0 else -1)


def crate_sprite_for_type(crate_type):
    if crate_type == BOMB_TYPE:
        return bomb_sprite
    if crate_type == POWERUP_HELMET_TYPE:
        return crate_sprites[5]
    return crate_sprites[(crate_type - 1) % NUM_CRATE_TYPES]


class Personagem:
    PW = TILE_SIZE - 12 # Reduced width (28px) for easier navigation in 1-tile gaps
    PH = TILE_SIZE * 2

    def __init__(self, grid_x, grid_y, char_id):
        self.x = float(grid_x * TILE_SIZE + (TILE_SIZE - self.PW) // 2)
        self.y = float(grid_y * TILE_SIZE)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.char_id = char_id
        cdef = next(c for c in CHAR_DEFS if c["id"] == char_id)
        self.velocidade = cdef["speed"]
        self.gravidade = 0.5
        self.jump_force = cdef["jump"]
        self.super_jump_force = cdef["super_jump"]
        self.max_super_jumps = cdef["super_jumps"]
        self.max_bombs = cdef.get("bombs", 0)
        self.super_jumps_left = cdef["super_jumps"]
        self.bombs_left = self.max_bombs
        self.no_chao = False
        self.estado = "parado"
        self.dir = 1
        self.frame = 0
        self.anim_tick = 0
        self.alive = True
        self.stun_timer = 0
        self.jump_queued = False
        self.super_jump_queued = False
        self.jump_buffer = 0
        self.super_jump_buffer = 0
        self.coyote_timer = 0
        self.push_cooldown = 0
        self.bomb_cooldown = 0
        self.helmet_timer = 0
        self.sprites = char_sprites[char_id]
        self.num_frames = len(self.sprites)

    @property
    def grid_x(self):
        cx = self.x + self.PW / 2
        return max(0, min(COLS - 1, int(cx / TILE_SIZE)))

    @property
    def grid_y(self):
        cy = self.y + self.PH / 2
        return max(0, min(ROWS - 1, int(cy / TILE_SIZE)))

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.PW, self.PH)

    def pular(self):
        if self.alive and self.stun_timer <= 0:
            self.jump_queued = True
            self.jump_buffer = JUMP_BUFFER_FRAMES
            play_sound(sound_jump)

    def super_pular(self):
        if self.alive and self.stun_timer <= 0 and self.super_jumps_left > 0:
            self.super_jump_queued = True
            self.super_jump_buffer = JUMP_BUFFER_FRAMES
            play_sound(sound_super_jump)

    def ativar_stun(self, duracao=25):
        self.stun_timer = duracao
        self.vel_x = 0
        play_sound(sound_stun)

    def _proximo_caixa(self, board_ref):
        probe_top = self.y + self.PH / 3
        probe_height = max(8, self.PH - self.PH // 3)
        contact_slack = 3
        if self.dir == 1:
            probe_left = self.x + self.PW
            probe_right = probe_left + contact_slack
        else:
            probe_right = self.x
            probe_left = probe_right - contact_slack
            
        # Check falling boxes first
        for box in falling_boxes:
            bpx = box.get("px", box["x"] * TILE_SIZE)
            bpy = box.get("py", box["y"] * TILE_SIZE)
            tile_r = pygame.Rect(bpx, bpy, TILE_SIZE, TILE_SIZE)
            # For falling crates, check full player height so push triggers instantly without delay
            overlap_h = min(self.y + self.PH, tile_r.bottom) - max(self.y, tile_r.top)
            if overlap_h > 0:
                if self.dir == 1:
                    edge_gap = tile_r.left - (self.x + self.PW)
                else:
                    edge_gap = self.x - tile_r.right
                if 0 <= edge_gap <= contact_slack:
                    return ("falling", box)

        ty0 = max(0, int(probe_top // TILE_SIZE))
        ty1 = min(ROWS - 1, int((probe_top + probe_height - 1) // TILE_SIZE))
        tx0 = max(0, int(probe_left // TILE_SIZE))
        tx1 = min(COLS - 1, int((probe_right - 1) // TILE_SIZE))
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if board_ref[ty][tx] != 0:
                    tile_r = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    overlap_h = min(probe_top + probe_height, tile_r.bottom) - max(probe_top, tile_r.top)
                    if self.dir == 1:
                        edge_gap = tile_r.left - (self.x + self.PW)
                    else:
                        edge_gap = self.x - tile_r.right
                    if 0 <= edge_gap <= contact_slack and overlap_h >= TILE_SIZE // 3:
                        return ("board", tx, ty)
        return None

    def _pode_empurrar_para(self, board_ref, box_x, box_y):
        dst_x = box_x + self.dir
        if not (0 <= dst_x < COLS):
            return False
            
        # Can't push if destination is occupied
        if board_ref[box_y][dst_x] != 0:
            return False
            
        # Can't push if there's a crate on top of this one
        if box_y > 0 and board_ref[box_y - 1][box_x] != 0:
            return False
            
        # Prevent pushing if there is a falling box currently crossing that tile
        for b in falling_boxes:
            if b["x"] == dst_x:
                ty0 = int(b["py"] // TILE_SIZE)
                ty1 = int((b["py"] + TILE_SIZE - 1) // TILE_SIZE)
                if ty0 <= box_y <= ty1:
                    return False
        return True

    def atualizar(self, teclas, board_ref):
        if not self.alive:
            return

        if self.stun_timer > 0:
            self.stun_timer -= 1
            self.estado = "stun"
            self.vel_x = 0
            self._aplicar_fisica(board_ref)
            return

        if self.no_chao:
            self.coyote_timer = COYOTE_FRAMES
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        if self.jump_buffer > 0:
            self.jump_buffer -= 1
        if self.super_jump_buffer > 0:
            self.super_jump_buffer -= 1
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1
        if self.helmet_timer > 0:
            self.helmet_timer -= 1.0/60.0

        if self.push_cooldown > 0:
            moving_forward = (self.dir == -1 and teclas.get("esquerda")) or (self.dir == 1 and teclas.get("direita"))
            moving_backward = (self.dir == -1 and teclas.get("direita")) or (self.dir == 1 and teclas.get("esquerda"))
            
            if moving_forward:
                self.vel_x = PUSH_HORIZONTAL_SPEED * self.dir
                self.estado = "empurrando"
            elif moving_backward:
                # Cancel push cooldown and move back immediately
                self.push_cooldown = 0
                self.vel_x = -self.velocidade if self.dir == 1 else self.velocidade
                self.dir = -self.dir # Flip direction
                self.estado = "andando"
            else:
                self.vel_x = 0
                self.estado = "parado"
            
            if self.push_cooldown > 0:
                self.push_cooldown -= 1
        else:
            if teclas.get("esquerda"):
                self.vel_x = -self.velocidade
                self.dir = -1
            elif teclas.get("direita"):
                self.vel_x = self.velocidade
                self.dir = 1
            else:
                self.vel_x = 0
                if self.no_chao:
                    self.estado = "parado"

        if self.push_cooldown <= 0:
            prox = self._proximo_caixa(board_ref) if self.vel_x != 0 else None
            wants_to_push = prox is not None

            if wants_to_push:
                ptype = prox[0]
                pushed = False
                if ptype == "board":
                    bx, by = prox[1], prox[2]
                    nnx = bx + self.dir
                    if self._pode_empurrar_para(board_ref, bx, by):
                        self._empurrar_caixa(board_ref, bx, by, nnx)
                        self.push_cooldown = 16
                        pushed = True
                elif ptype == "falling":
                    box = prox[1]
                    bx = box["x"]
                    nnx = bx + self.dir
                    if 0 <= nnx < COLS:
                        ty0 = int(box["py"] // TILE_SIZE)
                        ty1 = min(ROWS - 1, int((box["py"] + TILE_SIZE - 1) // TILE_SIZE))
                        can_push_f = True
                        for ty in range(ty0, ty1 + 1):
                            if board_ref[ty][nnx] != 0: can_push_f = False
                        
                        if can_push_f and not any(b["x"] == nnx and abs(b["py"] - box["py"]) < TILE_SIZE for b in falling_boxes):
                            box["x"] = nnx
                            self.push_cooldown = 16
                            pushed = True
                
                if pushed:
                    self.vel_x = PUSH_HORIZONTAL_SPEED * self.dir
                    self.estado = "empurrando"
                    play_sound(sound_push)
                else:
                    self.vel_x = 0
            elif self.vel_x != 0 and self.no_chao:
                self.estado = "andando"
            elif self.vel_x == 0 and self.no_chao:
                self.estado = "parado"

        can_jump_from_ground = self.no_chao or self.coyote_timer > 0

        if self.super_jump_buffer > 0 and can_jump_from_ground and self.super_jumps_left > 0:
            self.vel_y = self.super_jump_force
            self.no_chao = False
            self.coyote_timer = 0
            self.estado = "pulando"
            self.super_jumps_left -= 1
            self.super_jump_queued = False
            self.super_jump_buffer = 0
            self.jump_queued = False
            self.jump_buffer = 0
        elif self.jump_buffer > 0 and can_jump_from_ground:
            self.vel_y = self.jump_force
            self.no_chao = False
            self.coyote_timer = 0
            self.estado = "pulando"
            self.jump_queued = False
            self.jump_buffer = 0

        self._aplicar_fisica(board_ref)

    def _aplicar_fisica(self, board_ref):
        self.vel_y += self.gravidade
        if self.vel_y > TILE_SIZE:
            self.vel_y = float(TILE_SIZE)

        self.x += self.vel_x
        self._resolver_horizontal(board_ref)

        self.y += self.vel_y
        self._resolver_vertical(board_ref)

        if self.x < 0:
            self.x = 0
            self.vel_x = 0
        if self.x + self.PW > WIDTH:
            self.x = float(WIDTH - self.PW)
            self.vel_x = 0

        self._atualizar_anim()

    def _resolver_horizontal(self, board_ref):
        global score
        r = self.rect
        y0 = max(0, r.top // TILE_SIZE)
        y1 = min(ROWS - 1, (r.bottom - 1) // TILE_SIZE)
        x0 = max(0, r.left // TILE_SIZE)
        x1 = min(COLS - 1, (r.right - 1) // TILE_SIZE)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if board_ref[ty][tx] != 0:
                    tile_r = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if not r.colliderect(tile_r):
                        continue
                    if board_ref[ty][tx] == POWERUP_HELMET_TYPE:
                        self.helmet_timer = 5.0 # 5 seconds
                        board_ref[ty][tx] = 0
                        score += 50
                        play_sound(sound_helmet)
                        global screen_shake
                        screen_shake = 10
                        add_particles(self.x + self.PW/2, self.y + self.PH/2, (100, 255, 100), 20)
                        continue
                        
                    if self.vel_x > 0:
                        self.x = float(tile_r.left - self.PW)
                    elif self.vel_x < 0:
                        self.x = float(tile_r.right)
                    else:
                        d_left = r.right - tile_r.left
                        d_right = tile_r.right - r.left
                        if d_left < d_right:
                            self.x = float(tile_r.left - self.PW)
                        else:
                            self.x = float(tile_r.right)
                    self.vel_x = 0
                    return
        
        # Check falling boxes horizontally
        r = self.rect # Re-fetch rect in case x was modified
        for box in falling_boxes:
            bpx = box.get("px", box["x"] * TILE_SIZE)
            bpy = box.get("py", box["y"] * TILE_SIZE)
            tile_r = pygame.Rect(bpx, bpy, TILE_SIZE, TILE_SIZE)
            if not r.colliderect(tile_r):
                continue
            # Make sure it's a true horizontal collision (not just bumping the bottom)
            overlap_h = min(r.bottom, tile_r.bottom) - max(r.top, tile_r.top)
            if overlap_h > 0:
                if self.vel_x > 0:
                    self.x = float(tile_r.left - self.PW)
                elif self.vel_x < 0:
                    self.x = float(tile_r.right)
                else:
                    d_left = r.right - tile_r.left
                    d_right = tile_r.right - r.left
                    if d_left < d_right:
                        self.x = float(tile_r.left - self.PW)
                    else:
                        self.x = float(tile_r.right)
                self.vel_x = 0
                return

    def _resolver_vertical(self, board_ref):
        global score
        self.no_chao = False
        r = self.rect
        y0 = max(0, r.top // TILE_SIZE)
        y1 = min(ROWS - 1, (r.bottom - 1) // TILE_SIZE)
        x0 = max(0, r.left // TILE_SIZE)
        x1 = min(COLS - 1, (r.right - 1) // TILE_SIZE)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if board_ref[ty][tx] == 0:
                    continue
                tile_r = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not r.colliderect(tile_r):
                    continue
                if board_ref[ty][tx] == POWERUP_HELMET_TYPE:
                    self.helmet_timer = 5.0 # 5 seconds
                    board_ref[ty][tx] = 0
                    score += 50
                    play_sound(sound_helmet)
                    continue
                    
                if self.vel_y > 0:
                    self.y = float(tile_r.top - self.PH)
                    self.vel_y = 0
                    self.no_chao = True
                elif self.vel_y < 0:
                    self.y = float(tile_r.bottom)
                    self.vel_y = 0
                return

        floor_y = ROWS * TILE_SIZE
        if self.y + self.PH >= floor_y:
            self.y = float(floor_y - self.PH)
            self.vel_y = 0
            self.no_chao = True

    def _empurrar_caixa(self, board_ref, from_x, from_y, to_x):
        crate_type = board_ref[from_y][from_x]
        board_ref[from_y][from_x] = 0
        landing_y = from_y
        while landing_y < ROWS - 1 and board_ref[landing_y + 1][to_x] == 0:
            landing_y += 1
            
        bt = 0
        if crate_type == BOMB_TYPE:
            bt = bomb_timers[from_y][from_x]
            bomb_timers[from_y][from_x] = 0 # Clear original
            
        register_push_animation(from_x, from_y, to_x, landing_y, crate_type, bomb_timer=bt)

    def _atualizar_anim(self):
        prev = getattr(self, '_last_estado', None)
        if prev != self.estado:
            self.anim_tick = 0
            self._last_estado = self.estado
            self.frame = 0

        self.anim_tick += 1

        walk_rate = max(2, int(5.5 - self.velocidade * 0.5))

        if self.estado == "empurrando":
            tick_rate = walk_rate + 3
        elif self.estado == "andando":
            tick_rate = walk_rate
        elif self.estado == "pulando":
            tick_rate = 999
        else:
            tick_rate = 10

        if self.anim_tick >= tick_rate:
            self.anim_tick = 0
            if self.estado == "andando":
                self.frame = (self.frame + 1) % len(WALK_RIGHT_FRAMES)
            elif self.estado == "empurrando":
                self.frame = (self.frame + 1) % len(PUSH_RIGHT_FRAMES)
            elif self.estado == "parado":
                self.frame = (self.frame + 1) % len(IDLE_FRAMES)

    def get_sprite(self):
        if not self.alive:
            idx = min(STUN_FRAME, self.num_frames - 1)
            return self.sprites[idx]

        if self.estado == "pulando":
            idx = JUMP_RIGHT_FRAME if self.dir == 1 else JUMP_LEFT_FRAME
            return self.sprites[min(idx, self.num_frames - 1)]

        if self.estado == "stun":
            return self.sprites[min(STUN_FRAME, self.num_frames - 1)]

        if self.estado == "empurrando":
            frames = PUSH_RIGHT_FRAMES if self.dir == 1 else PUSH_LEFT_FRAMES
            idx = frames[self.frame % len(frames)]
            return self.sprites[min(idx, self.num_frames - 1)]

        if self.estado == "andando":
            frames = WALK_RIGHT_FRAMES if self.dir == 1 else WALK_LEFT_FRAMES
            idx = frames[self.frame % len(frames)]
            return self.sprites[min(idx, self.num_frames - 1)]

        idx = IDLE_FRAMES[self.frame % len(IDLE_FRAMES)]
        return self.sprites[min(idx, self.num_frames - 1)]

    def check_falling_collision(self, falling_boxes_list):
        global score
        if not self.alive:
            return
        # Player body bounds for crate collision (tight)
        body_left = self.x + 8
        body_right = self.x + self.PW - 8
        body_top = self.y
        body_bottom = self.y + self.PH * 0.6  # upper 60% of character

        for box in falling_boxes_list[:]:
            box_px = box.get("px", box["x"] * TILE_SIZE)
            box_py = box.get("py", box["y"] * TILE_SIZE)

            # Horizontal check: tighter width, requires the player to be physically underneath
            crate_left = box_px + 4
            crate_right = box_px + TILE_SIZE - 4
            if body_right < crate_left or body_left > crate_right:
                continue

            # Vertical check: crate must be falling strictly from above
            crate_bottom = box_py + TILE_SIZE
            
            # If the crate's bottom is roughly at or below the player's top, it's a hit.
            # However, if the crate is already too far down (e.g., player walked sideways into it), 
            # it shouldn't crush.
            if crate_bottom < body_top or box_py > body_top + 16:
                continue
                
            if box["type"] == POWERUP_HELMET_TYPE:
                self.helmet_timer = 5.0 # 5 seconds
                score += 50
                play_sound(sound_powerup)
                global screen_shake
                screen_shake = 10
                add_particles(box_px + TILE_SIZE/2, box_py + TILE_SIZE/2, (100, 255, 100), 20)
                falling_boxes_list.remove(box)
                continue

            # Collision detected — check for break
            stomp_hit = (
                self.vel_y >= 0 and
                (self.y + self.PH) <= box_py + 16 and
                (self.y + self.PH / 2) < (box_py + TILE_SIZE / 2)
            )
            
            if stomp_hit:
                falling_boxes_list.remove(box)
                score += 10
                play_sound(sound_explode)
                self.vel_y = min(self.vel_y, -4)
                continue

            # Helmet protection: destroys anything hitting from above/head
            if self.helmet_timer > 0:
                falling_boxes_list.remove(box)
                score += 10
                play_sound(sound_explode)
                # Bouncing effect
                if self.vel_y < 0:
                    self.vel_y = 2
                floating_explosions.append({"px": box_px, "py": box_py, "timer": 20})
                continue

            # No protection and not a stomp -> Death
            self.alive = False
            stop_timers()
            stop_gameplay_music()
            play_sound(sound_game_over_sfx)
            play_music("gameover.mid")
            # Update Highscore
            char_id = self.char_id
            current_hs = highscores.get(char_id, 0)
            if score > current_hs:
                highscores[char_id] = score
                save_highscores(highscores)
            return

    def try_place_bomb(self, board_ref):
        global bomb_timers
        if self.bombs_left > 0 and self.bomb_cooldown <= 0:
            # Place at player's leg level in front of them
            tx = self.grid_x + self.dir
            ty = self.grid_y
            
            # Clamp tx/ty
            old_tx, old_ty = tx, ty
            tx = max(0, min(COLS - 1, tx))
            ty = max(0, min(ROWS - 1, ty))
            
            # If we are at the edge and trying to place outside, don't place on ourself
            if tx == self.grid_x:
                return False
            
            if board_ref[ty][tx] == BOMB_TYPE:
                # Target is already a bomb: do nothing
                return False
            else:
                # Replace whatever is there (empty or crate) with a 3s bomb
                board_ref[ty][tx] = BOMB_TYPE
                bomb_timers[ty][tx] = 180
            
            self.bombs_left -= 1
            self.bomb_cooldown = 40
            play_sound(sound_bomb)
            return True
        return False


board = []
helmet_timers = []
bomb_timers = []
player = None
falling_boxes = []
push_animations = []
score = 0
game_state = "title"
selected_char = 0
crane_x = 0.0
crane_vx = 0.0
cranes = []
crane_frame = 0
difficulty = 1.0
spawn_interval = INITIAL_SPAWN_MS
line_clear_flash = 0
combo_count = 0
match_anim_cells = []
match_anim_timer = 0


def reset_game(start_diff=1.0):
    global board, player, falling_boxes, push_animations, score, game_state
    global cranes, crane_frame, difficulty, spawn_interval
    global line_clear_flash, combo_count, match_anim_cells, match_anim_timer, helmet_timers, bomb_timers
    global screen_shake, particles
    screen_shake = 0
    particles = []
    char_id = CHAR_DEFS[selected_char]["id"]
    board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    helmet_timers = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    bomb_timers = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    player = Personagem(5, ROWS - 1, char_id)
    falling_boxes = []
    push_animations = []
    score = 0
    game_state = "play"
    cranes = []
    crane_frame = 0
    difficulty = float(start_diff)
    spawn_interval = max(800, int(INITIAL_SPAWN_MS / difficulty))
    line_clear_flash = 0
    combo_count = 0
    match_anim_cells = []
    match_anim_timer = 0
    pygame.time.set_timer(GRAVITY_EVENT, GRAVITY_MS)
    pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
    start_gameplay_music()


def stop_timers():
    pygame.time.set_timer(GRAVITY_EVENT, 0)
    pygame.time.set_timer(SPAWN_EVENT, 0)


def find_line_matches():
    matched = set()
    for y in range(ROWS):
        x = 0
        while x < COLS:
            t = board[y][x]
            if t == 0 or t == BOMB_TYPE:
                x += 1
                continue
            run = 1
            while x + run < COLS and board[y][x + run] == t:
                run += 1
            if run >= 3:
                for i in range(x, x + run):
                    matched.add((i, y))
            x += run
    for x in range(COLS):
        y = 0
        while y < ROWS:
            t = board[y][x]
            if t == 0 or t == BOMB_TYPE:
                y += 1
                continue
            run = 1
            while y + run < ROWS and board[y + run][x] == t:
                run += 1
            if run >= 3:
                for i in range(y, y + run):
                    matched.add((x, i))
            y += run
    return matched


def apply_board_gravity():
    for x in range(COLS):
        write_y = ROWS - 1
        for y in range(ROWS - 1, -1, -1):
            if board[y][x] != 0:
                if write_y != y:
                    board[write_y][x] = board[y][x]
                    helmet_timers[write_y][x] = helmet_timers[y][x]
                    bomb_timers[write_y][x] = bomb_timers[y][x]
                    board[y][x] = 0
                    helmet_timers[y][x] = 0
                    bomb_timers[y][x] = 0
                write_y -= 1


def do_post_landing():
    global combo_count, explosion_anim_cells, explosion_anim_timer, score
    global difficulty, spawn_interval, line_clear_flash
    
    to_explode = set()
    
    # Check for full line clears
    cleared = 0
    for y in range(ROWS):
        if all(board[y][x] != 0 for x in range(COLS)):
            cleared += 1
            for x in range(COLS):
                to_explode.add((x, y))
                
    if cleared > 0:
        score += 100 * cleared
        # Logarithmic difficulty scaling: starts fast but slows down later
        difficulty = 1.0 + math.log10(1 + score / 50.0) * 3.0
        spawn_interval = max(600, int(INITIAL_SPAWN_MS / difficulty)) 
        pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
        line_clear_flash = 15
        play_sound(sound_line_clear)
        update_gameplay_music()
        
        global screen_shake
        screen_shake = 15
        for mx, my in to_explode:
            add_particles(mx * TILE_SIZE, my * TILE_SIZE, (255, 255, 255), 15)

    # Check for match-3 combos
    matched = find_line_matches()
    if matched:
        combo_count += 1
        score += 50 * combo_count
        to_explode.update(matched)
        play_sound(sound_combo)
        for mx, my in matched:
            add_particles(mx * TILE_SIZE, my * TILE_SIZE, (255, 200, 50), 10)

    if to_explode:
        explosion_anim_cells = list(to_explode)
        explosion_anim_timer = 20
        for mx, my in to_explode:
            board[my][mx] = 0
            helmet_timers[my][mx] = 0
            bomb_timers[my][mx] = 0


def handle_bomb(bx, by):
    global score, explosion_anim_cells, explosion_anim_timer, screen_shake
    screen_shake = 20
    explosion_anim_cells = []
    play_sound(sound_explode)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            nx, ny = bx + dx, by + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                board[ny][nx] = 0
                bomb_timers[ny][nx] = 0
                explosion_anim_cells.append((nx, ny))
                
    explosion_anim_timer = 20  # 4 frames * 5 ticks
    
    # Helmet protects against explosions!
    if player and player.alive and player.helmet_timer > 0:
        # Player is safe
        pass
    elif player and player.alive:
        pgx, pgy = player.grid_x, player.grid_y
        # If player is anywhere in the 3x3 area (including the extra height of the character)
        p_row_top = player.grid_y
        p_row_bot = player.grid_y + 1 # Character is 2 tiles high
        
        in_x_range = abs(pgx - bx) <= 1
        in_y_range = (abs(p_row_top - by) <= 1) or (abs(p_row_bot - by) <= 1)
        
        if in_x_range and in_y_range:
            player.alive = False
            stop_timers()
            stop_gameplay_music()
            play_sound(sound_game_over_sfx)
            play_music("gameover.mid")
            return
    score += 30


def handle_gravity():
    if not player or not player.alive:
        return

    for box in falling_boxes[:]:
        landed = False
        if box["y"] == ROWS - 1:
            landed = True
        elif box["y"] + 1 < ROWS and board[box["y"] + 1][box["x"]] != 0:
            landed = True

        if landed:
            bx_pos, by_pos, btype = box["x"], box["y"], box["type"]
            board[by_pos][bx_pos] = btype
            if btype == POWERUP_HELMET_TYPE:
                helmet_timers[by_pos][bx_pos] = 180  # 3 seconds at 60 fps
            elif btype == BOMB_TYPE:
                bomb_timers[by_pos][bx_pos] = 180
            falling_boxes.remove(box)
            play_sound(sound_land)
            global screen_shake
            screen_shake = max(screen_shake, 3)
            pgx, pgy = player.grid_x, player.grid_y
            if pgx == bx_pos and pgy == by_pos:
                player.ativar_stun(15)
            if btype == BOMB_TYPE:
                handle_bomb(bx_pos, by_pos)
            else:
                global combo_count
                combo_count = 0
                do_post_landing()
        else:
            box["y"] += 1


def register_push_animation(from_x, from_y, to_x, landing_y, crate_type, bomb_timer=0):
    slide_target_px = to_x * TILE_SIZE
    slide_target_py = from_y * TILE_SIZE
    final_target_py = landing_y * TILE_SIZE
    push_animations.append({
        "x": to_x,
        "y": landing_y,
        "type": crate_type,
        "px": from_x * TILE_SIZE,
        "py": from_y * TILE_SIZE,
        "target_px": slide_target_px,
        "target_py": slide_target_py,
        "final_py": final_target_py,
        "stage": "slide",
        "bomb_timer": bomb_timer
    })


def current_crane_count():
    return max(1, min(CRANE_COUNT, int(difficulty)))


def queue_crate_spawn(grid_x, crate_type):
    active_count = current_crane_count()
    if len(cranes) >= active_count:
        return
    
    speed = 2.0 + difficulty * 0.2
    if random.choice([True, False]):
        x = -CRANE_SPRITE_W
        vx = speed
    else:
        x = WIDTH + CRANE_SPRITE_W
        vx = -speed
        
    cranes.append({
        "x": float(x),
        "vx": float(vx),
        "drop_x": grid_x,
        "type": crate_type,
        "dropped": False
    })


def update_crane():
    global crane_frame
    crane_frame = 0
    for c in cranes[:]:
        prev_x = c["x"]
        c["x"] += c["vx"]
        
        if not c["dropped"]:
            target_px = c["drop_x"] * TILE_SIZE + TILE_SIZE / 2
            curr_hook = c["x"] + CRANE_SPRITE_W / 2
            prev_hook = prev_x + CRANE_SPRITE_W / 2
            
            crossed = (
                (c["vx"] > 0 and prev_hook <= target_px <= curr_hook) or
                (c["vx"] < 0 and prev_hook >= target_px >= curr_hook)
            )
            
            if crossed:
                drop_row = max(0, CRANE_SPRITE_H // TILE_SIZE)
                falling_boxes.append({
                    "x": c["drop_x"],
                    "y": drop_row,
                    "type": c["type"],
                    "px": float(c["drop_x"] * TILE_SIZE),
                    "py": float(CRANE_SPRITE_H),
                })
                c["dropped"] = True
                
        if c["vx"] > 0 and c["x"] > WIDTH + CRANE_SPRITE_W:
            cranes.remove(c)
        elif c["vx"] < 0 and c["x"] < -CRANE_SPRITE_W * 2:
            cranes.remove(c)


def update_box_visuals():
    for box in falling_boxes:
        target_px = float(box["x"] * TILE_SIZE)
        target_py = float(box["y"] * TILE_SIZE)
        if "px" not in box:
            box["px"] = target_px
            box["py"] = target_py
        bpx_diff = abs(target_px - box["px"])
        bpy_diff = abs(target_py - box["py"])
        if bpx_diff > 0.5:
            box["px"] = approach(box["px"], target_px, max(14, bpx_diff * 0.9))
        else:
            box["px"] = target_px
        if bpy_diff > 0.5:
            box["py"] = approach(box["py"], target_py, max(16, bpy_diff * 0.95))
        else:
            box["py"] = target_py

    completed_pushes = []
    for anim in push_animations[:]:
        px_diff = abs(anim["target_px"] - anim["px"])
        py_diff = abs(anim["target_py"] - anim["py"])
        if px_diff > 0.5:
            horizontal_speed = PUSH_HORIZONTAL_SPEED if anim["stage"] == "slide" else PUSH_SLIDE_SPEED
            anim["px"] = approach(anim["px"], anim["target_px"], max(horizontal_speed, px_diff * 0.18))
        else:
            anim["px"] = anim["target_px"]
        if py_diff > 0.5:
            anim["py"] = approach(anim["py"], anim["target_py"], max(12, py_diff * 0.55))
        else:
            anim["py"] = anim["target_py"]
        if anim["px"] == anim["target_px"] and anim["py"] == anim["target_py"]:
            if anim["stage"] == "slide" and anim["final_py"] != anim["target_py"]:
                anim["stage"] = "fall"
                anim["target_py"] = anim["final_py"]
            else:
                completed_pushes.append(anim)
                push_animations.remove(anim)

    # Update floating explosions (if any)
    for exp in floating_explosions[:]:
        exp["timer"] -= 1
        if exp["timer"] <= 0:
            floating_explosions.remove(exp)

    global combo_count
    for anim in completed_pushes:
        board[anim["y"]][anim["x"]] = anim["type"]
        if anim["type"] == POWERUP_HELMET_TYPE:
            helmet_timers[anim["y"]][anim["x"]] = anim.get("helmet_timer", 180)
        
        if anim["type"] == BOMB_TYPE:
            # Transfer the fuse timer to the new location
            bomb_timers[anim["y"]][anim["x"]] = anim.get("bomb_timer", 180)
        
        combo_count = 0
        apply_board_gravity()
        do_post_landing()


def draw_hud_to(target_surf):
    # Background panel
    pygame.draw.rect(target_surf, (18, 22, 32), (0, HEIGHT, WIDTH, HUD_H))
    pygame.draw.line(target_surf, (50, 60, 80), (0, HEIGHT), (WIDTH, HEIGHT), 2)
    
    # Left side: Score
    txt_pts = font_med.render(f"PONTOS {score}", True, (255, 210, 50))
    target_surf.blit(txt_pts, (10, HEIGHT + 12))
    
    # Center-Left: Super Jumps (shifted to avoid overlap with PONTOS)
    if player and player.max_super_jumps > 0:
        sj_color = (100, 220, 255) if player.super_jumps_left > 0 else (100, 100, 120)
        sj_txt = font_med.render(f"SUPER {player.super_jumps_left}", True, sj_color)
        # Position it further to the right to avoid overlapping with high scores
        screen_center = WIDTH // 2
        target_surf.blit(sj_txt, (screen_center - 20, HEIGHT + 12))
        
    # Right side: Level and Bombs
    lvl = int(difficulty)
    lvl_txt = font_sm.render(f"NIVEL {lvl}", True, (180, 200, 220))
    target_surf.blit(lvl_txt, (WIDTH - lvl_txt.get_width() - 15, HEIGHT + 10))
    
    if player and getattr(player, "max_bombs", 0) > 0:
        b_color = (255, 100, 100) if player.bombs_left > 0 else (120, 80, 80)
        b_txt = font_sm.render(f"BOMBAS {player.bombs_left}", True, b_color)
        target_surf.blit(b_txt, (WIDTH - b_txt.get_width() - 15, HEIGHT + 30))
        
    # Overlays for active states
    if player and player.helmet_timer > 0:
        h_secs = math.ceil(player.helmet_timer)
        h_txt = font_sm.render(f"CAPACETE {h_secs}", True, (100, 255, 100))
        target_surf.blit(h_txt, (10, HEIGHT + 32))
        
    if combo_count > 1:
        combo_txt = font_sm.render(f"COMBO X{combo_count}!", True, (255, 150, 50))
        target_surf.blit(combo_txt, (WIDTH // 2 - combo_txt.get_width() // 2, HEIGHT + 32))


def draw_hud():
    draw_hud_to(screen)


def draw_crane():
    if not crane_sprites:
        return
    crane_w = CRANE_SPRITE_W

    # Draw horizontal rail across top of screen
    rail_y = CRANE_Y + 2
    pygame.draw.rect(screen, (100, 70, 50), (0, rail_y, WIDTH, 5))
    pygame.draw.rect(screen, (160, 120, 80), (0, rail_y + 1, WIDTH, 3))

    for c in cranes:
        cx = c["x"]
        if cx + crane_w < 0 or cx > WIDTH:
            continue
        if not c["dropped"]:
            crate_type = c["type"]
            frame_idx = CRANE_FRAME_FOR_CRATE.get(crate_type, 0)
        else:
            frame_idx = CRANE_EMPTY_FRAME
        frame_idx = min(frame_idx, len(crane_sprites) - 1)
        sprite = crane_sprites[frame_idx]
        screen.blit(sprite, (int(cx), CRANE_Y))

def draw_game(flip=True):
    global screen_shake
    screen.fill((0, 0, 0)) # Clear screen to prevent ghosting during shake
    offset_x = 0
    offset_y = 0
    if screen_shake > 0:
        offset_x = random.randint(-screen_shake, screen_shake)
        offset_y = random.randint(-screen_shake, screen_shake)
        screen_shake -= 1

    temp_surface = pygame.Surface((WIDTH, HEIGHT + HUD_H))
    temp_surface.blit(bg_img, (0, 0))

    if line_clear_flash > 0:
        flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = int(min(180, line_clear_flash * 18))
        flash_surf.fill((255, 255, 255, alpha))
        temp_surface.blit(flash_surf, (0, 0))

    animated_cells = {(anim["x"], anim["y"]) for anim in push_animations}
    for y in range(ROWS):
        for x in range(COLS):
            if board[y][x] != 0 and (x, y) not in animated_cells:
                if board[y][x] == POWERUP_HELMET_TYPE:
                    ht = helmet_timers[y][x]
                    if 0 < ht < 60 and (ht // 5) % 2 == 0:
                        continue
                elif board[y][x] == BOMB_TYPE:
                    bt = bomb_timers[y][x]
                    if 0 < bt < 60 and (bt // 5) % 2 == 0:
                        continue
                temp_surface.blit(crate_sprite_for_type(board[y][x]), (x * TILE_SIZE, y * TILE_SIZE))
                
                # Bomb fuse spark animation (floating slightly ABOVE the bomb crate)
                if board[y][x] == BOMB_TYPE:
                    spark_x = x * TILE_SIZE + 20
                    spark_y = y * TILE_SIZE - 5
                    if (pygame.time.get_ticks() // 80) % 2 == 0:
                        # Add a tiny wiggle to simulate fire
                        wx = spark_x + random.randint(-1, 1)
                        wy = spark_y + random.randint(-1, 1)
                        pygame.draw.circle(temp_surface, (255, 220, 100), (wx, wy), random.randint(2, 4))
                        pygame.draw.circle(temp_surface, (255, 255, 255), (wx, wy), 1)

    if explosion_anim_timer > 0:
        exp_frame = 10 + (4 - ((explosion_anim_timer - 1) // 5) - 1)
        exp_frame = max(10, min(13, exp_frame))
        for mx, my in explosion_anim_cells:
            temp_surface.blit(crate_sprites[exp_frame], (mx * TILE_SIZE, my * TILE_SIZE))

    for exp in floating_explosions[:]:
        exp_frame = 10 + (4 - ((exp["timer"] - 1) // 5) - 1)
        exp_frame = max(10, min(13, exp_frame))
        temp_surface.blit(crate_sprites[exp_frame], (int(exp["px"]), int(exp["py"])))

    for box in falling_boxes:
        bpx = box.get("px", box["x"] * TILE_SIZE)
        bpy = box.get("py", box["y"] * TILE_SIZE)
        temp_surface.blit(crate_sprite_for_type(box["type"]), (int(bpx), int(bpy)))
        
        # Spark for falling bombs (floating slightly ABOVE)
        if box["type"] == BOMB_TYPE:
            spark_x = int(bpx) + 20
            spark_y = int(bpy) - 5
            if (pygame.time.get_ticks() // 80) % 2 == 0:
                wx = spark_x + random.randint(-1, 1)
                wy = spark_y + random.randint(-1, 1)
                pygame.draw.circle(temp_surface, (255, 220, 100), (wx, wy), random.randint(2, 4))

    for anim in push_animations:
        temp_surface.blit(crate_sprite_for_type(anim["type"]), (int(anim["px"]), int(anim["py"])))

    # Draw horizontal rail
    rail_y = CRANE_Y + 2
    pygame.draw.rect(temp_surface, (100, 70, 50), (0, rail_y, WIDTH, 5))
    pygame.draw.rect(temp_surface, (160, 120, 80), (0, rail_y + 1, WIDTH, 3))

    for c in cranes:
        cx = c["x"]
        if cx + CRANE_SPRITE_W < 0 or cx > WIDTH:
            continue
        if not c["dropped"]:
            frame_idx = CRANE_FRAME_FOR_CRATE.get(c["type"], 0)
        else:
            frame_idx = CRANE_EMPTY_FRAME
        frame_idx = min(frame_idx, len(crane_sprites) - 1)
        temp_surface.blit(crane_sprites[frame_idx], (int(cx), CRANE_Y))

    if player.alive:
        sprite = player.get_sprite()
        draw_x = player.x + (player.PW - sprite.get_width()) / 2
        draw_y = player.y + player.PH - sprite.get_height()
        if not (player.estado == "stun" and player.stun_timer % 6 < 3):
            temp_surface.blit(sprite, (int(draw_x), int(draw_y)))
    
    # Particles
    for p in particles:
        size = max(1, p["life"] // 8)
        pygame.draw.rect(temp_surface, p["color"], (int(p["x"]), int(p["y"]), size, size))

    # Draw HUD (Calls the dedicated function for consistency)
    draw_hud_to(temp_surface)

    if not player.alive:
        overlay = pygame.Surface((WIDTH, HEIGHT + HUD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        temp_surface.blit(overlay, (0, 0))
        
        panel_w, panel_h = 300, 260
        panel_x = WIDTH // 2 - panel_w // 2
        panel_y = HEIGHT // 2 - panel_h // 2
        
        # Background blur-like panel
        pygame.draw.rect(temp_surface, (10, 10, 15), (panel_x + 6, panel_y + 6, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(temp_surface, (35, 40, 55), (panel_x, panel_y, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(temp_surface, (255, 60, 60), (panel_x, panel_y, panel_w, panel_h), width=4, border_radius=20)
        
        # Title (Jetpack Style)
        t_go = render_styled_text("GAME OVER", font_big, (255, 255, 255), 
                                  outline_color=(60, 0, 0), outline_width=4,
                                  gradient=((255, 100, 100), (180, 20, 20)))
        temp_surface.blit(t_go, (WIDTH // 2 - t_go.get_width() // 2, panel_y + 15))
        
        # Character Icon
        icon = char_icons[CHAR_DEFS[selected_char]["id"]]
        temp_surface.blit(icon, (WIDTH // 2 - icon.get_width() // 2, panel_y + 55))
        
        # Score display
        score_val = font_med.render(str(score), True, (255, 255, 255))
        temp_surface.blit(score_val, (WIDTH // 2 - score_val.get_width() // 2, panel_y + 145))
        score_lbl = font_xs.render("PONTOS TOTAIS", True, (140, 150, 170))
        temp_surface.blit(score_lbl, (WIDTH // 2 - score_lbl.get_width() // 2, panel_y + 172))

        # Record logic
        char_id = CHAR_DEFS[selected_char]["id"]
        best = highscores.get(char_id, 0)
        is_new = score >= best and score > 0
        
        hs_col = (100, 255, 100) if is_new else (255, 210, 50)
        hs_msg = "NOVO RECORDE" if is_new else f"RECORDE {best}"
        t_hs = font_sm.render(hs_msg, True, hs_col)
        temp_surface.blit(t_hs, (WIDTH // 2 - t_hs.get_width() // 2, panel_y + 200))
        
        # Instructions
        instr = font_sm.render("R REINICIAR   Q SAIR", True, (200, 210, 230))
        temp_surface.blit(instr, (WIDTH // 2 - instr.get_width() // 2, panel_y + 232))

    # Final blit with shake
    screen.fill((0, 0, 0))
    screen.blit(temp_surface, (offset_x, offset_y))
    if flip:
        pygame.display.flip()

def draw_retro_tv(content_type="pause", timer=0):
    overlay = pygame.Surface((WIDTH, HEIGHT + HUD_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # TV Body (Bigger)
    tv_w, tv_h = 320, 240
    tv_x = WIDTH // 2 - tv_w // 2
    tv_y = (HEIGHT + HUD_H) // 2 - tv_h // 2
    pygame.draw.rect(screen, (70, 65, 60), (tv_x, tv_y, tv_w, tv_h), border_radius=20)
    pygame.draw.rect(screen, (30, 25, 20), (tv_x, tv_y, tv_w, tv_h), width=8, border_radius=20)
    
    # TV Screen Area
    screen_w, screen_h = 240, 180
    screen_x = tv_x + 20
    screen_y = tv_y + 25
    pygame.draw.rect(screen, (15, 15, 15), (screen_x-4, screen_y-4, screen_w+8, screen_h+8), border_radius=10)
    
    if content_type == "pause":
        # Static noise
        for _ in range(150):
            nx = random.randint(screen_x, screen_x + screen_w - 4)
            ny = random.randint(screen_y, screen_y + screen_h - 4)
            c = random.randint(80, 180)
            pygame.draw.rect(screen, (c, c, c), (nx, ny, 4, 4))
        
        # "PAUSE" text
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            p_txt = font_big.render("PAUSE", True, (0, 255, 0))
            screen.blit(p_txt, (screen_x + screen_w // 2 - p_txt.get_width() // 2, screen_y + screen_h // 2 - 20))
    
    elif content_type == "ad":
        # Ad Content inside TV
        pygame.draw.rect(screen, (240, 235, 210), (screen_x, screen_y, screen_w, screen_h), border_radius=5)
        
        ad_title = font_med.render("CRATE COLA", True, (200, 30, 30))
        screen.blit(ad_title, (screen_x + screen_w // 2 - ad_title.get_width() // 2, screen_y + 20))
        
        ad_slogan = font_xs.render("Beba e pule alto!", True, (40, 40, 40))
        screen.blit(ad_slogan, (screen_x + screen_w // 2 - ad_slogan.get_width() // 2, screen_y + 55))
        
        # Small crate drawing in ad
        pygame.draw.rect(screen, (139, 69, 19), (screen_x + screen_w // 2 - 20, screen_y + 80, 40, 40))
        pygame.draw.rect(screen, (100, 50, 10), (screen_x + screen_w // 2 - 20, screen_y + 80, 40, 40), 2)
        
        t_txt = font_xs.render(f"Voltando em {timer}...", True, (80, 80, 80))
        screen.blit(t_txt, (screen_x + screen_w // 2 - t_txt.get_width() // 2, screen_y + 140))

    # Scanlines (Always on)
    for row in range(screen_y, screen_y + screen_h, 4):
        s = pygame.Surface((screen_w, 2), pygame.SRCALPHA)
        s.fill((0, 0, 0, 80))
        screen.blit(s, (screen_x, row))
        
    # Knobs & Antennas
    pygame.draw.circle(screen, (25, 20, 15), (tv_x + 290, tv_y + 60), 12)
    pygame.draw.circle(screen, (25, 20, 15), (tv_x + 290, tv_y + 110), 12)
    pygame.draw.line(screen, (90, 90, 90), (tv_x + 100, tv_y), (tv_x + 40, tv_y - 70), 5)
    pygame.draw.line(screen, (90, 90, 90), (tv_x + 100, tv_y), (tv_x + 160, tv_y - 60), 5)

    pygame.display.flip()

def draw_pause_overlay():
    draw_retro_tv("pause")

def draw_ad(timer):
    # The ad content is drawn inside the TV frame
    seconds = max(0, timer // 60)
    draw_retro_tv("ad", seconds)
    
    # Extra skip message at the bottom of the screen
    if seconds > 0:
        skip_msg = f"Aguarde {seconds}s..."
        col = (150, 150, 150)
    else:
        skip_msg = "PRESSIONE ENTER PARA PULAR"
        col = (0, 255, 0)
        
    s_txt = font_sm.render(skip_msg, True, col)
    screen.blit(s_txt, (WIDTH // 2 - s_txt.get_width() // 2, HEIGHT + HUD_H - 45))
    pygame.display.flip()


def draw_title():
    screen.blit(title_img, (0, 0))
    pulse = int(128 + 127 * abs((pygame.time.get_ticks() % 2000) / 1000 - 1))
    color = (pulse, pulse, 255)
    t = font_med.render("Pressione ENTER para jogar", True, color)
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT + HUD_H - 36))
    pygame.display.flip()


def draw_char_select():
    total_h = HEIGHT + HUD_H
    screen.fill((18, 22, 32))
    
    # Background grid pattern
    for i in range(0, WIDTH, 40):
        pygame.draw.line(screen, (25, 30, 45), (i, 0), (i, total_h))
    for j in range(0, total_h, 40):
        pygame.draw.line(screen, (25, 30, 45), (0, j), (WIDTH, j))

    # Title with heavy outline and gradient (Jetpack Style) - Adjusted for fit
    title_y = 15
    t_surf = render_styled_text("SELECIONE O PERSONAGEM", font_big, (255, 255, 255), 
                                outline_color=(10, 20, 50), outline_width=3, 
                                gradient=((255, 255, 255), (180, 200, 255)))
    screen.blit(t_surf, (WIDTH // 2 - t_surf.get_width() // 2, title_y))
    
    pygame.draw.line(screen, (255, 210, 50), (40, title_y + 45), (WIDTH - 40, title_y + 45), 3)

    cols = 3
    rows = 2
    margin_x = 30
    margin_y = 100
    spacing_x = 18
    spacing_y = 22
    
    total_cards_w = WIDTH - (margin_x * 2)
    total_cards_h = total_h - (margin_y + 50)
    cell_w = (total_cards_w - (cols - 1) * spacing_x) // cols
    cell_h = (total_cards_h - (rows - 1) * spacing_y) // rows

    for i, cdef in enumerate(CHAR_DEFS):
        r = i // cols
        c = i % cols
        is_sel = (i == selected_char)
        
        rx = margin_x + c * (cell_w + spacing_x)
        ry = margin_y + r * (cell_h + spacing_y)
        cx = rx + cell_w // 2
        
        # Floating animation for selected card
        if is_sel:
            ry -= int(5 * abs(math.sin(pygame.time.get_ticks() * 0.005)))

        rect = pygame.Rect(rx, ry, cell_w, cell_h)

        # Selection Glow
        if is_sel:
            for thickness in range(1, 5):
                alpha = 150 // thickness
                s = pygame.Surface((cell_w + thickness*2, cell_h + thickness*2), pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 210, 50, alpha), s.get_rect(), border_radius=12, width=1)
                screen.blit(s, (rx - thickness, ry - thickness))
            
        fill_col = (45, 52, 70) if is_sel else (32, 36, 48)
        border_col = (255, 210, 50) if is_sel else (60, 65, 80)
        
        # Shadow
        pygame.draw.rect(screen, (10, 12, 18), (rx + 5, ry + 5, cell_w, cell_h), border_radius=10)
        # Card Body
        pygame.draw.rect(screen, fill_col, rect, border_radius=10)
        pygame.draw.rect(screen, border_col, rect, 3 if is_sel else 1, border_radius=10)

        # "EQUIPADO" Tag
        if is_sel:
            tag_w, tag_h = 76, 20
            pygame.draw.rect(screen, (255, 210, 50), (cx - tag_w//2, ry - 10, tag_w, tag_h), border_radius=5)
            tag_txt = font_xs.render("EQUIPADO", True, (20, 20, 25))
            screen.blit(tag_txt, (cx - tag_txt.get_width()//2, ry - 8))

        # Sprite logic - Reduced to give more room for text
        sprites = char_sprites[cdef["id"]]
        if sprites:
            char_spr = sprites[0]
            spr_h = int(cell_h * 0.35) # Reduced from 0.42
            spr_w = int(spr_h * char_spr.get_width() / char_spr.get_height())
            scaled_spr = pygame.transform.scale(char_spr, (spr_w, spr_h))
            # Shadow under sprite
            pygame.draw.ellipse(screen, (0, 0, 0, 130), (cx - 15, ry + 15 + spr_h - 4, 30, 7))
            screen.blit(scaled_spr, (cx - spr_w // 2, ry + 15))
            sprite_bottom = ry + 15 + spr_h

        # Name & Record (Outlined for mobile look) - Remove hyphens and colons
        name_str = cdef["name"].upper().replace("-", " ")
        name_parts = name_str.split(" ")
        # Group parts to keep it to max 2 lines
        if len(name_parts) == 3:
            name_parts = [name_parts[0] + " " + name_parts[1], name_parts[2]]
        
        name_y = sprite_bottom + 2
        for part in name_parts:
            # Use styled text for names too
            p_font = font_xs if len(part) > 9 else font_sm
            p_surf = render_styled_text(part, p_font, (255, 255, 255) if is_sel else (180, 190, 200),
                                        outline_color=(0, 0, 0), outline_width=2)
            screen.blit(p_surf, (cx - p_surf.get_width() // 2, name_y))
            name_y += 12 if p_font == font_xs else 14
        
        rec = highscores.get(cdef["id"], 0)
        # Outlined record (removed colon for font compatibility)
        r_col = (255, 210, 50) if rec > 0 else (120, 130, 145)
        rec_surf = render_styled_text(f"RECORDE {rec}", font_xs, r_col, outline_width=1)
        screen.blit(rec_surf, (cx - rec_surf.get_width() // 2, name_y))

        # Stats bars with Icons - Adjusted for spacing
        bar_y = name_y + 18
        bar_w = cell_w - 55
        bar_x = rx + 38
        
        # Speed (Lightning Bolt Icon) - Scaled down
        bolt_x, bolt_y = rx + 16, bar_y - 2
        s = 0.8 # Scale factor
        bolt_pts = [
            (bolt_x+5*s, bolt_y), (bolt_x+13*s, bolt_y), 
            (bolt_x+7*s, bolt_y+7*s), (bolt_x+14*s, bolt_y+7*s), 
            (bolt_x+3*s, bolt_y+18*s), (bolt_x+7*s, bolt_y+10*s), 
            (bolt_x+1*s, bolt_y+10*s)
        ]
        
        pygame.draw.polygon(screen, (10, 10, 10), bolt_pts, width=2)
        pygame.draw.polygon(screen, (255, 235, 50), bolt_pts)
        pygame.draw.line(screen, (255, 255, 255), (bolt_x+5*s, bolt_y+1), (bolt_x+10*s, bolt_y+1), 1)
        
        pygame.draw.rect(screen, (22, 24, 32), (bar_x, bar_y, bar_w, 7), border_radius=3)
        v_fill = int(bar_w * (cdef['speed'] / 5.0))
        pygame.draw.rect(screen, (70, 150, 255), (bar_x, bar_y, v_fill, 7), border_radius=3)

        # Jump (Up Arrow Icon) - Symmetric and pixel-aligned
        bar_y += 16
        arrow_x, arrow_y = rx + 16, bar_y - 2
        # Use fixed integer coords for perfect symmetry
        tri_pts = [(arrow_x+6, arrow_y), (arrow_x, arrow_y+8), (arrow_x+12, arrow_y+8)]
        # Outline
        pygame.draw.polygon(screen, (10, 10, 10), tri_pts, width=3)
        pygame.draw.rect(screen, (10, 10, 10), (arrow_x+2, arrow_y+7, 8, 9))
        # Base Fill
        pygame.draw.polygon(screen, (100, 200, 50), tri_pts)
        pygame.draw.rect(screen, (100, 200, 50), (arrow_x+3, arrow_y+8, 6, 7))
        # Shading (Right half)
        pygame.draw.polygon(screen, (60, 140, 30), [(arrow_x+6, arrow_y+1), (arrow_x+11, arrow_y+7), (arrow_x+6, arrow_y+7)])
        pygame.draw.rect(screen, (60, 140, 30), (arrow_x+6, arrow_y+8, 3, 7))
        # Highlight
        pygame.draw.line(screen, (255, 255, 255), (arrow_x+3, arrow_y+7), (arrow_x+5, arrow_y+3), 1)
        
        pygame.draw.rect(screen, (22, 24, 32), (bar_x, bar_y, bar_w, 7), border_radius=3)
        j_fill = int(bar_w * (cdef['super_jumps'] / 5.0))
        pygame.draw.rect(screen, (70, 255, 130), (bar_x, bar_y, j_fill, 7), border_radius=3)

        # Bomb perk badge - Cleaned up to fit and avoid font tofus
        if cdef.get("bombs", 0) > 0:
            bar_y += 14
            pygame.draw.rect(screen, (210, 45, 45), (cx - 32, bar_y, 64, 12), border_radius=6)
            b_txt = font_xs.render("BOMBAS", True, (255, 255, 255))
            screen.blit(b_txt, (cx - b_txt.get_width()//2, bar_y - 4))

    # Footer navigation bar
    footer_y = total_h - 45
    pygame.draw.rect(screen, (15, 18, 25), (0, footer_y, WIDTH, 45))
    pygame.draw.line(screen, (50, 55, 75), (0, footer_y), (WIDTH, footer_y), 2)
    
    instr = [("SETAS", "Navegar"), ("ENTER", "Jogar"), ("ESC", "Sair")]
    total_instr_w = sum(font_sm.size(k)[0] + font_sm.size(f" {t}    ")[0] for k, t in instr)
    ix = (WIDTH - total_instr_w) // 2
    for key, txt in instr:
        k_r = font_sm.render(key, True, (255, 210, 50))
        t_r = font_sm.render(f" {txt}    ", True, (210, 215, 230))
        screen.blit(k_r, (ix, footer_y + 12))
        ix += k_r.get_width()
        screen.blit(t_r, (ix, footer_y + 12))
        ix += t_r.get_width()

    pygame.display.flip()


def draw_level_select():
    total_h = HEIGHT + HUD_H
    for y_line in range(total_h):
        t = y_line / total_h
        r = int(25 + 10 * t)
        g = int(30 + 15 * t)
        b = int(45 + 20 * t)
        if (y_line // 3) % 2 == 0:
            r = max(0, r - 5); g = max(0, g - 5); b = max(0, b - 5)
        pygame.draw.line(screen, (r, g, b), (0, y_line), (WIDTH, y_line))

    pygame.draw.rect(screen, (15, 20, 30), (0, 0, WIDTH, 50))
    pygame.draw.line(screen, (255, 200, 50), (0, 50), (WIDTH, 50), 3)
    
    title_text = "Selecione a Dificuldade"
    t_shadow = font_big.render(title_text, True, (0, 0, 0))
    t_main = font_big.render(title_text, True, (255, 255, 255))
    screen.blit(t_shadow, (WIDTH // 2 - t_main.get_width() // 2 + 2, 12))
    screen.blit(t_main, (WIDTH // 2 - t_main.get_width() // 2, 10))
    
    levels = [
        ("Nivel 1", "1 Guindaste"),
        ("Nivel 2", "2 Guindastes"),
        ("Nivel 3", "3 Guindastes")
    ]
    
    start_y = 120
    spacing = 100
    
    for i, (name, desc) in enumerate(levels):
        is_sel = (i + 1 == selected_level)
        rect = pygame.Rect(WIDTH // 2 - 120, start_y + i * spacing, 240, 80)
        
        shadow_rect = rect.copy()
        shadow_rect.y += 6
        pygame.draw.rect(screen, (10, 10, 15, 180), shadow_rect, border_radius=10)
        
        fill_col = (60, 68, 85) if is_sel else (35, 40, 55)
        border_col = (255, 210, 50) if is_sel else (20, 25, 35)
        border_width = 4 if is_sel else 2
        pygame.draw.rect(screen, fill_col, rect, border_radius=10)
        pygame.draw.rect(screen, border_col, rect, border_width, border_radius=10)
        
        name_col = (255, 255, 255) if is_sel else (180, 190, 200)
        n_txt = font_med.render(name, True, name_col)
        d_txt = font_sm.render(desc, True, (150, 200, 255) if is_sel else (100, 120, 150))
        
        screen.blit(n_txt, (WIDTH // 2 - n_txt.get_width() // 2, rect.y + 15))
        screen.blit(d_txt, (WIDTH // 2 - d_txt.get_width() // 2, rect.y + 45))
        
    keys = [("SETAS", "Selecionar"), ("ENTER", "Jogar"), ("ESC", "Voltar")]
    footer_y = total_h - 22
    total_keys_w = 0
    key_renders = []
    for key, label in keys:
        k_surf = font_xs.render(key, True, (255, 220, 100))
        l_surf = font_xs.render(f" {label}  ", True, (150, 155, 170))
        key_renders.append((k_surf, l_surf))
        total_keys_w += k_surf.get_width() + l_surf.get_width()
    draw_kx = WIDTH // 2 - total_keys_w // 2
    for k_surf, l_surf in key_renders:
        screen.blit(k_surf, (draw_kx, footer_y))
        draw_kx += k_surf.get_width()
        screen.blit(l_surf, (draw_kx, footer_y))
        draw_kx += l_surf.get_width()

    pygame.display.flip()

def run_game():
    global selected_level, game_state, selected_char, line_clear_flash, explosion_anim_timer
    ad_timer = 0
    selected_level = 1
    game_state = "title"
    play_music("title.mid", loops=-1)

    while True:
        dt = clock.get_time()

        if game_state == "title":
            draw_title()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        play_sound(sound_menu_select)
                        stop_music()
                        game_state = "char_select"
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
            clock.tick(30)

        elif game_state == "char_select":
            draw_char_select()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        play_sound(sound_menu_move)
                        game_state = "title"
                        play_music("title.mid", loops=-1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        play_sound(sound_menu_select)
                        game_state = "level_select"
                    elif event.key == pygame.K_LEFT:
                        selected_char = (selected_char - 1) % len(CHAR_DEFS)
                        play_sound(sound_menu_move)
                    elif event.key == pygame.K_RIGHT:
                        selected_char = (selected_char + 1) % len(CHAR_DEFS)
                        play_sound(sound_menu_move)
                    elif event.key == pygame.K_UP:
                        selected_char = (selected_char - 3) % len(CHAR_DEFS)
                        play_sound(sound_menu_move)
                    elif event.key == pygame.K_DOWN:
                        selected_char = (selected_char + 3) % len(CHAR_DEFS)
                        play_sound(sound_menu_move)
            clock.tick(30)

        elif game_state == "level_select":
            draw_level_select()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        play_sound(sound_menu_move)
                        game_state = "char_select"
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        play_sound(sound_menu_select)
                        stop_music()
                        reset_game(selected_level)
                    elif event.key == pygame.K_UP:
                        selected_level = max(1, selected_level - 1)
                        play_sound(sound_menu_move)
                    elif event.key == pygame.K_DOWN:
                        selected_level = min(3, selected_level + 1)
                        play_sound(sound_menu_move)
            clock.tick(30)

        elif game_state == "play":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if not player.alive:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            stop_music()
                            reset_game(selected_level)
                        elif event.key == pygame.K_q:
                            pygame.quit()
                            sys.exit()
                    continue

                if event.type == SPAWN_EVENT:
                    x = random.randint(0, COLS - 1)
                    r = random.random()
                    if r < 0.06:
                        ctype = BOMB_TYPE
                    elif r < 0.10:
                        ctype = POWERUP_HELMET_TYPE
                    else:
                        ctype = random.randint(1, NUM_CRATE_TYPES)
                    queue_crate_spawn(x, ctype)

                if event.type == GRAVITY_EVENT:
                    handle_gravity()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        stop_timers()
                        pause_music()
                        game_state = "pause"
                        continue
                    if event.key in (pygame.K_UP, pygame.K_w):
                        player.pular()
                    elif event.key == pygame.K_SPACE:
                        player.super_pular()
                    elif event.key == pygame.K_b:
                        player.try_place_bomb(board)

            # --- Logic outside the event loop ---
            if player.alive:
                keys = pygame.key.get_pressed()
                teclas = {
                    "esquerda": keys[pygame.K_LEFT] or keys[pygame.K_a],
                    "direita": keys[pygame.K_RIGHT] or keys[pygame.K_d],
                }
                player.atualizar(teclas, board)
                player.check_falling_collision(falling_boxes)
                update_crane()
                update_particles()

            if line_clear_flash > 0:
                line_clear_flash -= 1
            if explosion_anim_timer > 0:
                explosion_anim_timer -= 1
                if explosion_anim_timer == 0:
                    explosion_anim_cells = [] # Clear cells when timer ends
                    apply_board_gravity()
                    do_post_landing()

            needs_gravity = False
            for y in range(ROWS):
                for x in range(COLS):
                    if board[y][x] == POWERUP_HELMET_TYPE:
                        if helmet_timers[y][x] > 0:
                            helmet_timers[y][x] -= 1
                            if helmet_timers[y][x] <= 0:
                                board[y][x] = 0
                                needs_gravity = True
                    elif board[y][x] == BOMB_TYPE:
                        if bomb_timers[y][x] > 0:
                            bomb_timers[y][x] -= 1
                            if bomb_timers[y][x] <= 0:
                                handle_bomb(x, y)
            if needs_gravity:
                apply_board_gravity()
                do_post_landing()

            update_box_visuals()

            draw_game()
            clock.tick(60)

        elif game_state == "pause":
            draw_game(flip=False)
            draw_pause_overlay()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        play_sound(sound_menu_select)
                        game_state = "ad"
                        ad_timer = 180 # 3 seconds at 60fps
            clock.tick(60)

        elif game_state == "ad":
            draw_ad(ad_timer)
            if ad_timer > 0:
                ad_timer -= 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE) and ad_timer <= 0:
                        play_sound(sound_menu_select)
                        unpause_music()
                        pygame.time.set_timer(GRAVITY_EVENT, GRAVITY_MS)
                        pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
                        game_state = "play"
            clock.tick(60)


if __name__ == "__main__":
    run_game()
