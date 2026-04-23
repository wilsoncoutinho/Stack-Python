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
bomb_sprite = pygame.transform.scale(load_img("extracted/bomb.png"), (TILE_SIZE, TILE_SIZE))
crane_sprites = slice_sheet(load_img("extracted/crane.png"), 8, 18, TILE_SIZE / 8)

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
CRANE_SPACING = 84
CRANE_Y = 0
CRATE_HANG_Y = 18

for cdef in CHAR_DEFS:
    sheet = load_img("StackAttack2/" + cdef["sprite"])
    frames = slice_sheet(sheet, 8, 16, TILE_SIZE / 16)
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
    PW = TILE_SIZE - 8
    PH = TILE_SIZE

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
                        return tx, ty
        return None

    def _pode_empurrar_para(self, board_ref, box_x, box_y):
        dst_x = box_x + self.dir
        if not (0 <= dst_x < COLS):
            return False
        return board_ref[box_y][dst_x] == 0

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
            bx, by = prox
            nnx = bx + self.dir
            if can_push_now and self._pode_empurrar_para(board_ref, bx, by):
                self._empurrar_caixa(board_ref, bx, by, nnx)
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
                if board_ref[ty][tx] == 0:
                    continue
                tile_r = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not r.colliderect(tile_r):
                    continue
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
        r = self.rect
        for box in falling_boxes_list[:]:
            box_px = box.get("px", box["x"] * TILE_SIZE)
            box_py = box.get("py", box["y"] * TILE_SIZE)
            box_r = pygame.Rect(int(box_px), int(box_py), TILE_SIZE, TILE_SIZE)
            if r.colliderect(box_r):
                stomp_hit = (
                    self.vel_y >= 0 and
                    r.bottom <= box_r.top + 10 and
                    r.centery < box_r.centery
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
crane_x = 0
crane_target_x = 0
pending_spawns = []
active_crane_spawn = None
crane_frame = 0
crane_vx = 0.0
difficulty = 1.0
spawn_interval = INITIAL_SPAWN_MS
line_clear_flash = 0
combo_count = 0
match_anim_cells = []
match_anim_timer = 0


def reset_game():
    global board, player, falling_boxes, push_animations, score, game_state
    global crane_x, crane_target_x, pending_spawns, active_crane_spawn, crane_frame, crane_vx, difficulty, spawn_interval
    global line_clear_flash, combo_count, match_anim_cells, match_anim_timer
    char_id = CHAR_DEFS[selected_char]["id"]
    board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    player = Personagem(5, ROWS - 1, char_id)
    falling_boxes = []
    push_animations = []
    score = 0
    game_state = "play"
    crane_x = 0
    crane_target_x = 0
    pending_spawns = []
    active_crane_spawn = None
    crane_frame = 0
    crane_vx = 0.0
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


def check_lines():
    global score, difficulty, spawn_interval, line_clear_flash
    y = ROWS - 1
    cleared = 0
    while y >= 0:
        if all(board[y][x] != 0 for x in range(COLS)):
            del board[y]
            board.insert(0, [0 for _ in range(COLS)])
            score += 100
            cleared += 1
        else:
            y -= 1
    if cleared > 0:
        difficulty = 1.0 + score / 800
        spawn_interval = max(800, int(INITIAL_SPAWN_MS / difficulty))
        pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
        line_clear_flash = 15
        play_music("fullrow.mid")


def do_post_landing():
    global combo_count, match_anim_cells, match_anim_timer
    changed = True
    combo_count = 0
    while changed:
        matched = find_line_matches()
        if matched:
            combo_count += 1
            score += 50 * combo_count
            match_anim_cells = list(matched)
            match_anim_timer = 8
            for mx, my in matched:
                board[my][mx] = 0
            apply_board_gravity()
            check_lines()
            changed = True
        else:
            changed = False


def handle_bomb(bx, by):
    global score
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            nx, ny = bx + dx, by + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                board[ny][nx] = 0
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
    do_post_landing()


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
            if abs(pgx - bx_pos) <= 1 and abs(pgy - by_pos) <= 1 and pgy == by_pos:
                player.ativar_stun(15)
            if btype == BOMB_TYPE:
                handle_bomb(bx_pos, by_pos)
            else:
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


def queue_crate_spawn(grid_x, crate_type):
    if active_crane_spawn is not None or pending_spawns:
        return
    pending_spawns.append({"x": grid_x, "type": crate_type})


def current_crane_count():
    return max(1, min(CRANE_COUNT, int(difficulty)))


def update_crane():
    global crane_x, crane_target_x, active_crane_spawn, crane_frame, crane_vx
    crane_width = crane_sprites[0].get_width() if crane_sprites else TILE_SIZE
    active_count = current_crane_count()
    convoy_width = crane_width + CRANE_SPACING * (active_count - 1)
    min_x = float(-(convoy_width - crane_width))
    max_x = 0.0

    if active_crane_spawn is None and pending_spawns:
        active_crane_spawn = pending_spawns.pop(0)
        crane_target_x = active_crane_spawn["x"] * TILE_SIZE + TILE_SIZE / 2
        active_crane_spawn["dropped"] = False

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

    if active_crane_spawn is None:
        crane_frame = 0
        return

    target_px = crane_target_x
    crossed_target = False
    for idx in range(active_count):
        prev_hook = prev_x + idx * CRANE_SPACING + crane_width / 2
        curr_hook = crane_x + idx * CRANE_SPACING + crane_width / 2
        if (
            not active_crane_spawn["dropped"] and (
                (crane_vx > 0 and prev_hook <= target_px <= curr_hook) or
                (crane_vx < 0 and prev_hook >= target_px >= curr_hook)
            )
        ):
            crossed_target = True
            break

    crane_frame = 0

    if crossed_target:
        falling_boxes.append({
            "x": active_crane_spawn["x"],
            "y": 0,
            "type": active_crane_spawn["type"],
            "px": float(active_crane_spawn["x"] * TILE_SIZE),
            "py": -float(TILE_SIZE),
        })
        active_crane_spawn = None


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

    for anim in completed_pushes:
        board[anim["y"]][anim["x"]] = anim["type"]
        if anim["type"] == BOMB_TYPE:
            handle_bomb(anim["x"], anim["y"])
        else:
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
    sprite = crane_sprites[min(crane_frame, len(crane_sprites) - 1)]
    crane_width = sprite.get_width()
    active_count = current_crane_count()

    closest_idx = None
    if active_crane_spawn is not None:
        target_px = active_crane_spawn["x"] * TILE_SIZE + TILE_SIZE / 2
        best_dist = None
        for idx in range(active_count):
            hook_x = crane_x + idx * CRANE_SPACING + crane_width / 2
            dist = abs(hook_x - target_px)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                closest_idx = idx

    for idx in range(active_count):
        draw_x = crane_x + idx * CRANE_SPACING
        if draw_x + crane_width < 0 or draw_x > WIDTH:
            continue
        screen.blit(sprite, (int(draw_x), CRANE_Y))
        if active_crane_spawn is not None and idx == closest_idx:
            crate_x = draw_x + crane_width / 2 - TILE_SIZE / 2
            screen.blit(crate_sprite_for_type(active_crane_spawn["type"]), (int(crate_x), CRATE_HANG_Y))


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

    if match_anim_timer > 0:
        for mx, my in match_anim_cells:
            s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            a = int(min(200, match_anim_timer * 30))
            s.fill((255, 255, 100, a))
            screen.blit(s, (mx * TILE_SIZE, my * TILE_SIZE))

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
    screen.fill((20, 25, 40))
    total_h = HEIGHT + HUD_H

    t = font_med.render("Escolha Personagem", True, (255, 220, 100))
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 10))

    cols_per_row = 3
    rows_count = 2
    margin_x = 8
    margin_y = 6
    top_y = 40
    cell_w = (WIDTH - margin_x * 2) // cols_per_row
    cell_h = (total_h - top_y - 30 - margin_y * rows_count) // rows_count

    for i, cdef in enumerate(CHAR_DEFS):
        row = i // cols_per_row
        col = i % cols_per_row
        cx = margin_x + col * cell_w + cell_w // 2
        cy = top_y + row * (cell_h + margin_y) + cell_h // 2

        is_sel = (i == selected_char)
        border_col = (255, 220, 100) if is_sel else (60, 70, 90)
        fill_col = (45, 55, 75) if is_sel else (30, 35, 50)

        rect = pygame.Rect(margin_x + col * cell_w + 4, top_y + row * (cell_h + margin_y), cell_w - 8, cell_h)
        pygame.draw.rect(screen, fill_col, rect, border_radius=4)
        pygame.draw.rect(screen, border_col, rect, 2 if is_sel else 1, border_radius=4)

        icon = char_icons[cdef["id"]]
        ih = min(int(cell_h * 0.45), 36)
        iw = int(ih * 0.5)
        icon_scaled = pygame.transform.scale(icon, (iw, ih))
        screen.blit(icon_scaled, (cx - icon_scaled.get_width() // 2, rect.top + 4))

        name_txt = font_sm.render(cdef["name"], True, (255, 255, 255) if is_sel else (180, 180, 180))
        screen.blit(name_txt, (cx - name_txt.get_width() // 2, rect.top + ih + 6))

        stats = "Vel:%.1f SuperPulos:%d" % (cdef["speed"], cdef["super_jumps"])
        stats_txt = font_xs.render(stats, True, (150, 180, 220))
        screen.blit(stats_txt, (cx - stats_txt.get_width() // 2, rect.top + ih + 24))

        if cdef["bomb"]:
            bomb_txt = font_xs.render("+ Bombas", True, (255, 150, 80))
            screen.blit(bomb_txt, (cx - bomb_txt.get_width() // 2, rect.top + ih + 38))

    keys_txt = font_xs.render("<- -> Selecionar  ENTER Jogar  ESC Voltar", True, (140, 150, 180))
    screen.blit(keys_txt, (WIDTH // 2 - keys_txt.get_width() // 2, total_h - 20))

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
                if event.key == pygame.K_UP:
                    player.pular()
                elif event.key == pygame.K_SPACE:
                    player.super_pular()
                elif event.key == pygame.K_b:
                    player.try_place_bomb(board)

        if player.alive:
            keys = pygame.key.get_pressed()
            teclas = {
                "esquerda": keys[pygame.K_LEFT],
                "direita": keys[pygame.K_RIGHT],
            }
            player.atualizar(teclas, board)
            player.check_falling_collision(falling_boxes)
            update_crane()

            if player.bomb_cooldown > 0:
                player.bomb_cooldown -= 1

            if line_clear_flash > 0:
                line_clear_flash -= 1
            if match_anim_timer > 0:
                match_anim_timer -= 1

            update_box_visuals()

        draw_game()
        clock.tick(60)
