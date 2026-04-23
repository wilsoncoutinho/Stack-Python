import pygame
import sys
import random
import os

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
font_big = pygame.font.SysFont("consolas", 32, bold=True)
font_med = pygame.font.SysFont("consolas", 22)
font_sm = pygame.font.SysFont("consolas", 18)
font_xs = pygame.font.SysFont("consolas", 14)

MAGENTA = (255, 0, 255)
NUM_CRATE_TYPES = 5
BOMB_TYPE = 8
GRAVITY_MS = 300
INITIAL_SPAWN_MS = 3000
GRAVITY_EVENT = pygame.USEREVENT + 1
SPAWN_EVENT = pygame.USEREVENT + 2


def load_img(rel_path, colorkey=MAGENTA):
    path = os.path.join(ASSETS, rel_path)
    img = pygame.image.load(path).convert()
    img.set_colorkey(colorkey)
    return img


def slice_sheet(sheet, fw, fh, scale=1.0):
    frames = []
    for i in range(sheet.get_width() // fw):
        sub = sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh))
        w = max(1, int(fw * scale))
        h = max(1, int(fh * scale))
        frames.append(pygame.transform.scale(sub, (w, h)))
    return frames


bg_img = pygame.transform.scale(load_img("extracted/back.png"), (WIDTH, HEIGHT))
title_img = pygame.transform.scale(load_img("extracted/title.png"), (WIDTH, HEIGHT + HUD_H))

crate_sprites = slice_sheet(load_img("extracted/crates.png"), 8, 8, TILE_SIZE / 8)
_bomb_img = pygame.image.load(os.path.join(ASSETS, "extracted/bomb_new.png")).convert_alpha()
bomb_sprite = pygame.transform.scale(_bomb_img, (TILE_SIZE, TILE_SIZE))

explosion_anim_cells = []
explosion_anim_timer = 0

# Crane sprites: full 16x18 frames (mechanism + crate built-in), scaled uniformly
CRANE_FW = 16  # actual frame width in the sprite sheet
crane_sprites = slice_sheet(load_img("extracted/crane.png"), CRANE_FW, 18, TILE_SIZE / 8)
# Frame mapping: crane frame index for each crate type (1-5) and empty
# Frame 0=yellow, 1=red, 2=green-striped, 3=blue, 4=red-variant, ..., 10=empty
CRANE_EMPTY_FRAME = 10
CRANE_FRAME_FOR_CRATE = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}  # crate_type -> crane frame
CRANE_SPRITE_W = crane_sprites[0].get_width() if crane_sprites else TILE_SIZE * 2
CRANE_SPRITE_H = crane_sprites[0].get_height() if crane_sprites else TILE_SIZE * 2

CHAR_DEFS = [
    {"id": "pete", "name": "Part-time Pete", "sprite": "man.png", "icon": "iconman.png",
     "speed": 3.5, "jump": -7.5, "super_jump": -10.5, "super_jumps": 0, "bomb": False,
     "desc": "Basico. Sem super pulos."},
    {"id": "lizzie", "name": "Lazy Lizzie", "sprite": "woman.png", "icon": "icwoman.png",
     "speed": 4.5, "jump": -7.0, "super_jump": -11.5, "super_jumps": 4, "bomb": False,
     "desc": "Rapida. 4 super pulos."},
    {"id": "frank", "name": "Forklift Frank", "sprite": "man2.png", "icon": "iconman2.png",
     "speed": 4.5, "jump": -8.0, "super_jump": -12.0, "super_jumps": 1, "bomb": False,
     "desc": "Rapido, 1 super pulo."},
    {"id": "will", "name": "Warehouse Will", "sprite": "man3.png", "icon": "iconman3.png",
     "speed": 4.0, "jump": -7.5, "super_jump": -11.5, "super_jumps": 2, "bomb": False,
     "desc": "Agil. 2 super pulos."},
    {"id": "cath", "name": "Crate-Crazy Cath", "sprite": "woman2.png", "icon": "icwoman2.png",
     "speed": 5.0, "jump": -7.5, "super_jump": -12.0, "super_jumps": 3, "bomb": False,
     "desc": "Muito rapida. 3 super pulos."},
    {"id": "sam", "name": "Super-Stacker Sam", "sprite": "man4.png", "icon": "iconman4.png",
     "speed": 5.0, "jump": -8.0, "super_jump": -13.0, "super_jumps": 5, "bomb": True,
     "desc": "O melhor! 5 super pulos + bombas."},
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
PUSH_SLIDE_SPEED = TILE_SIZE / 8
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


def approach(a, b, speed):
    diff = b - a
    if abs(diff) <= speed:
        return b
    return a + speed * (1 if diff > 0 else -1)


def crate_sprite_for_type(crate_type):
    if crate_type == BOMB_TYPE:
        return bomb_sprite
    return crate_sprites[(crate_type - 1) % NUM_CRATE_TYPES]


class Personagem:
    PW = TILE_SIZE - 4
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
        self.can_bomb = cdef["bomb"]
        self.super_jumps_left = cdef["super_jumps"]
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

    def super_pular(self):
        if self.alive and self.stun_timer <= 0 and self.super_jumps_left > 0:
            self.super_jump_queued = True
            self.super_jump_buffer = JUMP_BUFFER_FRAMES

    def ativar_stun(self, duracao=25):
        self.stun_timer = duracao
        self.vel_x = 0

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

        prox = self._proximo_caixa(board_ref) if self.vel_x != 0 and self.no_chao else None
        wants_to_push = prox is not None
        can_push_now = wants_to_push and self.push_cooldown <= 0

        if wants_to_push:
            self.estado = "empurrando"
            self.vel_x = 0
            if can_push_now:
                ptype = prox[0]
                if ptype == "board":
                    bx, by = prox[1], prox[2]
                    nnx = bx + self.dir
                    if self._pode_empurrar_para(board_ref, bx, by):
                        self._empurrar_caixa(board_ref, bx, by, nnx)
                        self.push_cooldown = 12
                elif ptype == "falling":
                    box = prox[1]
                    bx = box["x"]
                    nnx = bx + self.dir
                    # Check if destination is empty in board_ref and within bounds
                    if 0 <= nnx < COLS and board_ref[box["y"]][nnx] == 0:
                        # Ensure no other falling box is there
                        if not any(b["x"] == nnx and abs(b["py"] - box["py"]) < TILE_SIZE for b in falling_boxes):
                            box["x"] = nnx
                            self.push_cooldown = 12
        elif self.vel_x != 0 and self.no_chao:
            self.estado = "andando"
        elif self.vel_x == 0 and self.no_chao:
            self.estado = "parado"

        if self.push_cooldown > 0:
            self.push_cooldown -= 1

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
                    if self.vel_x > 0:
                        self.x = float(tile_r.left - self.PW)
                    elif self.vel_x < 0:
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
                self.vel_x = 0
                return

    def _resolver_vertical(self, board_ref):
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
        register_push_animation(from_x, from_y, to_x, landing_y, crate_type)

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

            # Collision detected — check for stomp
            stomp_hit = (
                self.vel_y >= 0 and
                (self.y + self.PH) <= box_py + 16 and
                (self.y + self.PH / 2) < (box_py + TILE_SIZE / 2)
            )
            if stomp_hit:
                falling_boxes_list.remove(box)
                score += 10
                self.vel_y = min(self.vel_y, -4)
            else:
                self.alive = False
                stop_timers()
                play_music("gameover.mid")
            return

    def try_place_bomb(self, board_ref):
        if not self.can_bomb or self.bomb_cooldown > 0:
            return False
        bx = self.grid_x + self.dir
        by = self.grid_y
        if not (0 <= bx < COLS and 0 <= by < ROWS):
            return False
        if board_ref[by][bx] != 0:
            handle_bomb(bx, by)
        else:
            board_ref[by][bx] = BOMB_TYPE
        self.bomb_cooldown = 30
        return True


board = []
player = None
falling_boxes = []
push_animations = []
score = 0
game_state = "title"
selected_char = 0
crane_x = 0.0
crane_vx = 0.0
crane_crates = {}       # {crane_index: {"x": grid_x, "type": crate_type}}
crane_frame = 0
difficulty = 1.0
spawn_interval = INITIAL_SPAWN_MS
line_clear_flash = 0
combo_count = 0
match_anim_cells = []
match_anim_timer = 0


def reset_game():
    global board, player, falling_boxes, push_animations, score, game_state
    global crane_x, crane_crates, crane_frame, crane_vx, difficulty, spawn_interval
    global line_clear_flash, combo_count, match_anim_cells, match_anim_timer
    char_id = CHAR_DEFS[selected_char]["id"]
    board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    player = Personagem(5, ROWS - 1, char_id)
    falling_boxes = []
    push_animations = []
    score = 0
    game_state = "play"
    crane_x = 0.0
    crane_crates = {}
    crane_frame = 0
    crane_vx = CRANE_SPEED
    difficulty = 1.0
    spawn_interval = INITIAL_SPAWN_MS
    line_clear_flash = 0
    combo_count = 0
    match_anim_cells = []
    match_anim_timer = 0
    pygame.time.set_timer(GRAVITY_EVENT, GRAVITY_MS)
    pygame.time.set_timer(SPAWN_EVENT, spawn_interval)


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
                    board[y][x] = 0
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
        difficulty = 1.0 + score / 800
        spawn_interval = max(800, int(INITIAL_SPAWN_MS / difficulty))
        pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
        line_clear_flash = 15
        play_music("fullrow.mid")

    # Check for match-3 combos
    matched = find_line_matches()
    if matched:
        combo_count += 1
        score += 50 * combo_count
        to_explode.update(matched)

    if to_explode:
        explosion_anim_cells = list(to_explode)
        explosion_anim_timer = 20
        for mx, my in to_explode:
            board[my][mx] = 0


def handle_bomb(bx, by):
    global score, explosion_anim_cells, explosion_anim_timer
    explosion_anim_cells = []
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            nx, ny = bx + dx, by + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                board[ny][nx] = 0
                explosion_anim_cells.append((nx, ny))
                
    explosion_anim_timer = 20  # 4 frames * 5 ticks

    if player and player.alive:
        pgx, pgy = player.grid_x, player.grid_y
        if abs(pgx - bx) <= 1 and abs(pgy - by) <= 1:
            pr = player.rect
            bomb_cx = bx * TILE_SIZE + TILE_SIZE // 2
            bomb_cy = by * TILE_SIZE + TILE_SIZE // 2
            pcx = player.x + player.PW // 2
            pcy = player.y + player.PH // 2
            dist = abs(pcx - bomb_cx) + abs(pcy - bomb_cy)
            if dist < TILE_SIZE * 1.5:
                player.alive = False
                stop_timers()
                play_music("gameover.mid")
                return
            player.ativar_stun(30)
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
            falling_boxes.remove(box)
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


def register_push_animation(from_x, from_y, to_x, landing_y, crate_type):
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
    })


def current_crane_count():
    return max(1, min(CRANE_COUNT, int(difficulty)))


def queue_crate_spawn(grid_x, crate_type):
    """Assign a crate to a free crane. Each crane carries independently."""
    active_count = current_crane_count()
    free = [i for i in range(active_count) if i not in crane_crates]
    if not free:
        return  # all cranes busy
    crane_idx = random.choice(free)
    crane_crates[crane_idx] = {"x": grid_x, "type": crate_type}


def update_crane():
    global crane_x, crane_vx, crane_frame, crane_crates
    slot_w = CRANE_SPRITE_W  # each crane slot is one sprite wide
    active_count = current_crane_count()
    convoy_width = slot_w + CRANE_SPACING * (active_count - 1)
    # Ensure hook center can reach from column 0 to column COLS-1
    min_x = float(-slot_w / 2)
    max_x = float(WIDTH - slot_w / 2)

    if crane_vx == 0:
        crane_vx = CRANE_SPEED

    prev_x = crane_x
    next_x = crane_x + crane_vx
    if next_x > max_x:
        crane_x = max_x
        crane_vx = -CRANE_SPEED
    elif next_x < min_x:
        crane_x = min_x
        crane_vx = CRANE_SPEED
    else:
        crane_x = next_x

    crane_frame = 0

    # Check each crane independently for dropping its crate
    dropped_indices = []
    for idx, crate_info in list(crane_crates.items()):
        if idx >= active_count:
            continue
        target_px = crate_info["x"] * TILE_SIZE + TILE_SIZE / 2
        prev_hook = prev_x + idx * CRANE_SPACING + slot_w / 2
        curr_hook = crane_x + idx * CRANE_SPACING + slot_w / 2
        crossed = (
            (crane_vx > 0 and prev_hook <= target_px <= curr_hook) or
            (crane_vx < 0 and prev_hook >= target_px >= curr_hook)
        )
        if crossed:
            # Start the crate at the crane's bottom position so it falls from there
            drop_row = max(0, CRANE_SPRITE_H // TILE_SIZE)
            falling_boxes.append({
                "x": crate_info["x"],
                "y": drop_row,
                "type": crate_info["type"],
                "px": float(crate_info["x"] * TILE_SIZE),
                "py": float(CRANE_SPRITE_H),
            })
            dropped_indices.append(idx)
    for idx in dropped_indices:
        del crane_crates[idx]


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

    global combo_count
    for anim in completed_pushes:
        board[anim["y"]][anim["x"]] = anim["type"]
        if anim["type"] == BOMB_TYPE:
            handle_bomb(anim["x"], anim["y"])
        else:
            combo_count = 0
            apply_board_gravity()
            do_post_landing()


def draw_hud():
    pygame.draw.rect(screen, (30, 35, 50), (0, HEIGHT, WIDTH, HUD_H))
    pygame.draw.line(screen, (80, 90, 110), (0, HEIGHT), (WIDTH, HEIGHT), 2)
    txt = font_med.render(f"Pontos: {score}", True, (255, 220, 100))
    screen.blit(txt, (10, HEIGHT + 12))
    if player and player.max_super_jumps > 0:
        sj_txt = font_sm.render(f"Super: {player.super_jumps_left}/{player.max_super_jumps}", True, (100, 220, 255))
        screen.blit(sj_txt, (WIDTH // 2 - sj_txt.get_width() // 2, HEIGHT + 15))
    lvl = int(difficulty)
    txt2 = font_sm.render(f"Nivel: {lvl}", True, (180, 200, 220))
    screen.blit(txt2, (WIDTH - txt2.get_width() - 10, HEIGHT + 15))
    if combo_count > 1:
        combo_txt = font_sm.render(f"Combo x{combo_count}!", True, (255, 150, 50))
        screen.blit(combo_txt, (WIDTH // 2 - combo_txt.get_width() // 2, HEIGHT + 32))


def draw_crane():
    if not crane_sprites:
        return
    active_count = current_crane_count()
    crane_w = CRANE_SPRITE_W

    # Draw horizontal rail across top of screen
    rail_y = CRANE_Y + 2
    pygame.draw.rect(screen, (100, 70, 50), (0, rail_y, WIDTH, 5))
    pygame.draw.rect(screen, (160, 120, 80), (0, rail_y + 1, WIDTH, 3))

    for idx in range(active_count):
        cx = crane_x + idx * CRANE_SPACING
        if cx + crane_w < 0 or cx > WIDTH:
            continue
        # Select correct sprite frame based on crate type
        if idx in crane_crates:
            crate_type = crane_crates[idx]["type"]
            frame_idx = CRANE_FRAME_FOR_CRATE.get(crate_type, 0)
        else:
            frame_idx = CRANE_EMPTY_FRAME
        frame_idx = min(frame_idx, len(crane_sprites) - 1)
        sprite = crane_sprites[frame_idx]
        screen.blit(sprite, (int(cx), CRANE_Y))


def draw_game():
    screen.blit(bg_img, (0, 0))

    if line_clear_flash > 0:
        flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = int(min(180, line_clear_flash * 18))
        flash_surf.fill((255, 255, 255, alpha))
        screen.blit(flash_surf, (0, 0))

    animated_cells = {(anim["x"], anim["y"]) for anim in push_animations}
    for y in range(ROWS):
        for x in range(COLS):
            if board[y][x] != 0 and (x, y) not in animated_cells:
                screen.blit(crate_sprite_for_type(board[y][x]), (x * TILE_SIZE, y * TILE_SIZE))

    if explosion_anim_timer > 0:
        # Frames from crate_sprites: indices 10, 11, 12, 13
        frame_idx = 3 - (explosion_anim_timer - 1) // 5
        frame_idx = max(0, min(3, frame_idx))
        exp_spr = pygame.transform.scale(crate_sprites[10 + frame_idx], (TILE_SIZE, TILE_SIZE))
        for mx, my in explosion_anim_cells:
            screen.blit(exp_spr, (mx * TILE_SIZE, my * TILE_SIZE))

    for box in falling_boxes:
        bpx = box.get("px", box["x"] * TILE_SIZE)
        bpy = box.get("py", box["y"] * TILE_SIZE)
        screen.blit(crate_sprite_for_type(box["type"]), (int(bpx), int(bpy)))

    for anim in push_animations:
        screen.blit(crate_sprite_for_type(anim["type"]), (int(anim["px"]), int(anim["py"])))

    draw_crane()

    if player.alive:
        sprite = player.get_sprite()
        draw_x = player.x + (player.PW - sprite.get_width()) / 2
        draw_y = player.y + player.PH - sprite.get_height()
        if player.estado == "stun" and player.stun_timer % 6 < 3:
            pass
        else:
            screen.blit(sprite, (int(draw_x), int(draw_y)))
    else:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))
        t1 = font_big.render("FIM DE JOGO", True, (255, 60, 60))
        screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 40))
        t2 = font_med.render(f"Pontos: {score}", True, (255, 255, 255))
        screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 10))
        t3 = font_sm.render("R - Reiniciar   Q - Sair", True, (200, 200, 200))
        screen.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 + 45))

    draw_hud()
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

    # Gradient background
    for y_line in range(total_h):
        t = y_line / total_h
        r = int(15 + 20 * t)
        g = int(18 + 15 * t)
        b = int(35 + 25 * t)
        pygame.draw.line(screen, (r, g, b), (0, y_line), (WIDTH, y_line))

    # Title with shadow
    title_text = "Escolha Personagem"
    t_shadow = font_big.render(title_text, True, (0, 0, 0))
    t_main = font_big.render(title_text, True, (255, 220, 100))
    screen.blit(t_shadow, (WIDTH // 2 - t_main.get_width() // 2 + 2, 12))
    screen.blit(t_main, (WIDTH // 2 - t_main.get_width() // 2, 10))

    # Decorative line under title
    line_y = 48
    pygame.draw.line(screen, (80, 70, 50), (30, line_y), (WIDTH - 30, line_y), 1)
    pygame.draw.line(screen, (255, 220, 100), (WIDTH // 2 - 60, line_y), (WIDTH // 2 + 60, line_y), 2)

    cols_per_row = 3
    rows_count = 2
    margin_x = 12
    margin_y = 10
    top_y = 58
    footer_h = 30
    cell_w = (WIDTH - margin_x * 2 - 8 * (cols_per_row - 1)) // cols_per_row
    cell_h = (total_h - top_y - footer_h - margin_y * (rows_count - 1)) // rows_count

    for i, cdef in enumerate(CHAR_DEFS):
        row = i // cols_per_row
        col = i % cols_per_row
        rx = margin_x + col * (cell_w + 8)
        ry = top_y + row * (cell_h + margin_y)
        cx = rx + cell_w // 2

        is_sel = (i == selected_char)

        rect = pygame.Rect(rx, ry, cell_w, cell_h)

        # Selected glow effect
        if is_sel:
            pulse = abs((pygame.time.get_ticks() % 1200) / 600 - 1)
            glow_alpha = int(40 + 30 * pulse)
            glow_surf = pygame.Surface((cell_w + 8, cell_h + 8), pygame.SRCALPHA)
            glow_surf.fill((255, 200, 80, glow_alpha))
            screen.blit(glow_surf, (rx - 4, ry - 4))

        # Card background
        fill_col = (50, 58, 80) if is_sel else (30, 35, 50)
        border_col = (255, 220, 100) if is_sel else (55, 60, 75)
        pygame.draw.rect(screen, fill_col, rect, border_radius=6)
        pygame.draw.rect(screen, border_col, rect, 3 if is_sel else 1, border_radius=6)

        # Character sprite (use actual game sprite, idle frame 0)
        sprites = char_sprites[cdef["id"]]
        if sprites:
            char_spr = sprites[0]
            # Scale to fit nicely in the card
            spr_h = min(int(cell_h * 0.50), 90)
            spr_w = int(spr_h * char_spr.get_width() / char_spr.get_height())
            scaled_spr = pygame.transform.scale(char_spr, (spr_w, spr_h))
            screen.blit(scaled_spr, (cx - spr_w // 2, ry + 8))
            sprite_bottom = ry + 8 + spr_h
        else:
            sprite_bottom = ry + 40

        # Character name
        name_col = (255, 255, 255) if is_sel else (170, 175, 190)
        name_txt = font_sm.render(cdef["name"], True, name_col)
        # Clip name if too wide
        name_x = cx - name_txt.get_width() // 2
        screen.blit(name_txt, (max(rx + 4, name_x), sprite_bottom + 4))

        # Stats
        stats_y = sprite_bottom + 22
        vel_txt = font_xs.render(f"Vel: {cdef['speed']:.1f}", True, (120, 180, 255))
        sj_txt = font_xs.render(f"Pulos: {cdef['super_jumps']}", True, (120, 220, 150))
        screen.blit(vel_txt, (rx + 8, stats_y))
        screen.blit(sj_txt, (rx + 8, stats_y + 14))

        if cdef["bomb"]:
            bomb_txt = font_xs.render("+ Bombas", True, (255, 150, 80))
            screen.blit(bomb_txt, (rx + 8, stats_y + 28))

    # Footer instructions
    keys = [("<- ->", "Selecionar"), ("ENTER", "Jogar"), ("ESC", "Voltar")]
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
                    game_state = "title"
                    play_music("title.mid", loops=-1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    stop_music()
                    reset_game()
                elif event.key == pygame.K_LEFT:
                    selected_char = (selected_char - 1) % len(CHAR_DEFS)
                elif event.key == pygame.K_RIGHT:
                    selected_char = (selected_char + 1) % len(CHAR_DEFS)
                elif event.key == pygame.K_UP:
                    selected_char = (selected_char - 3) % len(CHAR_DEFS)
                elif event.key == pygame.K_DOWN:
                    selected_char = (selected_char + 3) % len(CHAR_DEFS)
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
                        reset_game()
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
                continue

            if event.type == SPAWN_EVENT:
                x = random.randint(0, COLS - 1)
                if random.random() < 0.06:
                    ctype = BOMB_TYPE
                else:
                    ctype = random.randint(1, NUM_CRATE_TYPES)
                queue_crate_spawn(x, ctype)

            if event.type == GRAVITY_EVENT:
                handle_gravity()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    stop_timers()
                    stop_music()
                    game_state = "title"
                    play_music("title.mid", loops=-1)
                    continue
                if event.key in (pygame.K_UP, pygame.K_w):
                    player.pular()
                elif event.key == pygame.K_SPACE:
                    player.super_pular()
                elif event.key == pygame.K_b:
                    player.try_place_bomb(board)

        if player.alive:
            keys = pygame.key.get_pressed()
            teclas = {
                "esquerda": keys[pygame.K_LEFT] or keys[pygame.K_a],
                "direita": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            }
            player.atualizar(teclas, board)
            player.check_falling_collision(falling_boxes)
            update_crane()

            if player.bomb_cooldown > 0:
                player.bomb_cooldown -= 1

            if line_clear_flash > 0:
                line_clear_flash -= 1
            if explosion_anim_timer > 0:
                explosion_anim_timer -= 1
                if explosion_anim_timer == 0:
                    apply_board_gravity()
                    do_post_landing()

            update_box_visuals()

        draw_game()
        clock.tick(60)
