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
POWERUP_HELMET_TYPE = 5
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
_bomb_img = pygame.image.load(os.path.join(ASSETS, "extracted/black_bomb.png")).convert_alpha()
bomb_sprite = pygame.transform.scale(_bomb_img, (TILE_SIZE, TILE_SIZE))

explosion_anim_cells = []
floating_explosions = []
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

        if self.helmet_timer > 0:
            self.helmet_timer -= 1

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

        if self.push_cooldown > 0:
            if self.dir == -1 and teclas.get("esquerda"):
                self.vel_x = -PUSH_HORIZONTAL_SPEED
            elif self.dir == 1 and teclas.get("direita"):
                self.vel_x = PUSH_HORIZONTAL_SPEED
            else:
                self.vel_x = 0
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

        if self.push_cooldown > 0:
            if self.vel_x != 0:
                self.vel_x = PUSH_HORIZONTAL_SPEED * self.dir
                self.estado = "empurrando"
            self.push_cooldown -= 1
        else:
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
                        self.helmet_timer = 600
                        board_ref[ty][tx] = 0
                        score += 50
                        play_sound(sound_helmet)
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
                    self.helmet_timer = 600
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
                
            if box["type"] == POWERUP_HELMET_TYPE:
                self.helmet_timer = 600
                score += 50
                play_sound(sound_powerup)
                falling_boxes_list.remove(box)
                continue

            # Collision detected — check for break
            stomp_hit = (
                self.vel_y >= 0 and
                (self.y + self.PH) <= box_py + 16 and
                (self.y + self.PH / 2) < (box_py + TILE_SIZE / 2)
            )
            headbutt_hit = (
                self.vel_y < 0 and
                self.y <= crate_bottom and
                self.helmet_timer > 0
            )
            
            if stomp_hit:
                falling_boxes_list.remove(box)
                score += 10
                play_sound(sound_explode)
                self.vel_y = min(self.vel_y, -4)
            elif headbutt_hit:
                falling_boxes_list.remove(box)
                score += 10
                play_sound(sound_explode)
                self.vel_y = max(self.vel_y, 2)
                floating_explosions.append({"px": box_px, "py": box_py, "timer": 20})
            else:
                self.alive = False
                stop_timers()
                play_sound(sound_game_over_sfx)
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
        play_sound(sound_bomb)
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
    global line_clear_flash, combo_count, match_anim_cells, match_anim_timer
    char_id = CHAR_DEFS[selected_char]["id"]
    board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
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
        difficulty = 1.0 + score / 100.0
        spawn_interval = max(800, int(INITIAL_SPAWN_MS / difficulty))
        pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
        line_clear_flash = 15
        play_sound(sound_line_clear)
        play_music("fullrow.mid")

    # Check for match-3 combos
    matched = find_line_matches()
    if matched:
        combo_count += 1
        score += 50 * combo_count
        to_explode.update(matched)
        play_sound(sound_combo)

    if to_explode:
        explosion_anim_cells = list(to_explode)
        explosion_anim_timer = 20
        for mx, my in to_explode:
            board[my][mx] = 0


def handle_bomb(bx, by):
    global score, explosion_anim_cells, explosion_anim_timer
    explosion_anim_cells = []
    play_sound(sound_explode)
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
                play_sound(sound_game_over_sfx)
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
            play_sound(sound_land)
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
    active_count = current_crane_count()
    if len(cranes) >= active_count:
        return
    
    if random.choice([True, False]):
        x = -CRANE_SPRITE_W
        vx = CRANE_SPEED
    else:
        x = WIDTH + CRANE_SPRITE_W
        vx = -CRANE_SPEED
        
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
        
    if player and player.helmet_timer > 0:
        p_txt = font_sm.render(f"Poder(Cabecada): {player.helmet_timer // 60}s", True, (100, 255, 100))
        screen.blit(p_txt, (10, HEIGHT + 32))


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
        exp_frame = 10 + (4 - ((explosion_anim_timer - 1) // 5) - 1)
        exp_frame = max(10, min(13, exp_frame))
        for mx, my in explosion_anim_cells:
            screen.blit(crate_sprites[exp_frame], (mx * TILE_SIZE, my * TILE_SIZE))

    for exp in floating_explosions[:]:
        exp_frame = 10 + (4 - ((exp["timer"] - 1) // 5) - 1)
        exp_frame = max(10, min(13, exp_frame))
        screen.blit(crate_sprites[exp_frame], (int(exp["px"]), int(exp["py"])))
        exp["timer"] -= 1
        if exp["timer"] <= 0:
            floating_explosions.remove(exp)

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

    # Sleek industrial scanline background
    for y_line in range(total_h):
        t = y_line / total_h
        r = int(25 + 10 * t)
        g = int(30 + 15 * t)
        b = int(45 + 20 * t)
        if (y_line // 3) % 2 == 0:
            r = max(0, r - 5); g = max(0, g - 5); b = max(0, b - 5)
        pygame.draw.line(screen, (r, g, b), (0, y_line), (WIDTH, y_line))

    # Top Navigation Bar
    pygame.draw.rect(screen, (15, 20, 30), (0, 0, WIDTH, 50))
    pygame.draw.line(screen, (255, 200, 50), (0, 50), (WIDTH, 50), 3)
    
    title_text = "Selecione o Personagem"
    t_shadow = font_big.render(title_text, True, (0, 0, 0))
    t_main = font_big.render(title_text, True, (255, 255, 255))
    screen.blit(t_shadow, (WIDTH // 2 - t_main.get_width() // 2 + 2, 12))
    screen.blit(t_main, (WIDTH // 2 - t_main.get_width() // 2, 10))

    cols_per_row = 3
    rows_count = 2
    margin_x = 15
    margin_y = 15
    top_y = 65
    footer_h = 30
    cell_w = (WIDTH - margin_x * 2 - 10 * (cols_per_row - 1)) // cols_per_row
    cell_h = (total_h - top_y - footer_h - margin_y * (rows_count - 1)) // rows_count

    pulse = abs((pygame.time.get_ticks() % 1000) / 500 - 1)

    for i, cdef in enumerate(CHAR_DEFS):
        row = i // cols_per_row
        col = i % cols_per_row
        rx = margin_x + col * (cell_w + 10)
        ry = top_y + row * (cell_h + margin_y)
        cx = rx + cell_w // 2

        is_sel = (i == selected_char)

        # Selected card floats up slightly
        if is_sel:
            ry -= int(4 * pulse)

        rect = pygame.Rect(rx, ry, cell_w, cell_h)

        # Card shadow
        shadow_rect = rect.copy()
        shadow_rect.y += 6
        pygame.draw.rect(screen, (10, 10, 15, 180), shadow_rect, border_radius=10)

        # Card background (metallic gradient feel)
        fill_col = (60, 68, 85) if is_sel else (35, 40, 55)
        border_col = (255, 210, 50) if is_sel else (20, 25, 35)
        border_width = 4 if is_sel else 2
        pygame.draw.rect(screen, fill_col, rect, border_radius=10)
        pygame.draw.rect(screen, border_col, rect, border_width, border_radius=10)

        # Equipped Badge
        if is_sel:
            tag_rect = pygame.Rect(cx - 35, ry - 12, 70, 18)
            pygame.draw.rect(screen, (255, 210, 50), tag_rect, border_radius=8)
            tag_txt = font_xs.render("EQUIPADO", True, (0, 0, 0))
            screen.blit(tag_txt, (cx - tag_txt.get_width()//2, ry - 10))

        # Spotlight ellipse
        spot_surf = pygame.Surface((40, 15), pygame.SRCALPHA)
        pygame.draw.ellipse(spot_surf, (0, 0, 0, 120), (0, 0, 40, 15))
        screen.blit(spot_surf, (cx - 20, ry + int(cell_h * 0.45)))

        # Character sprite
        sprites = char_sprites[cdef["id"]]
        if sprites:
            char_spr = sprites[0]
            spr_h = min(int(cell_h * 0.45), 85)
            spr_w = int(spr_h * char_spr.get_width() / char_spr.get_height())
            scaled_spr = pygame.transform.scale(char_spr, (spr_w, spr_h))
            screen.blit(scaled_spr, (cx - spr_w // 2, ry + 12))
            sprite_bottom = ry + 12 + spr_h
        else:
            sprite_bottom = ry + 50

        # Character name
        name_col = (255, 255, 255) if is_sel else (180, 190, 200)
        parts = cdef["name"].split(' ')
        if len(parts) > 1:
            line1 = font_sm.render(parts[0], True, name_col)
            line2 = font_sm.render(" ".join(parts[1:]), True, name_col)
            screen.blit(line1, (cx - line1.get_width() // 2, sprite_bottom + 2))
            screen.blit(line2, (cx - line2.get_width() // 2, sprite_bottom + 16))
        else:
            name_txt = font_sm.render(cdef["name"], True, name_col)
            screen.blit(name_txt, (cx - name_txt.get_width() // 2, sprite_bottom + 9))

        # Progress bar stats
        stats_y = sprite_bottom + 38
        bar_x = rx + 32
        bar_w = cell_w - 40
        bar_h = 6

        # Speed
        vel_lbl = font_xs.render("VEL", True, (120, 180, 255))
        screen.blit(vel_lbl, (rx + 6, stats_y - 2))
        pygame.draw.rect(screen, (20, 25, 35), (bar_x, stats_y + 1, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (cdef['speed'] / 5.0))
        if fill_w > 0:
            pygame.draw.rect(screen, (50, 200, 255), (bar_x, stats_y + 1, fill_w, bar_h), border_radius=3)

        # Jumps
        stats_y += 16
        jmp_lbl = font_xs.render("PUL", True, (120, 220, 150))
        screen.blit(jmp_lbl, (rx + 6, stats_y - 2))
        pygame.draw.rect(screen, (20, 25, 35), (bar_x, stats_y + 1, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (cdef['super_jumps'] / 5.0))
        if fill_w > 0:
            pygame.draw.rect(screen, (100, 255, 150), (bar_x, stats_y + 1, fill_w, bar_h), border_radius=3)

        # Bomb perk
        if cdef["bomb"]:
            stats_y += 16
            bomb_rect = pygame.Rect(cx - 28, stats_y, 56, 14)
            pygame.draw.rect(screen, (200, 50, 50), bomb_rect, border_radius=4)
            bomb_txt = font_xs.render("+ BOMBAS", True, (255, 255, 255))
            screen.blit(bomb_txt, (cx - bomb_txt.get_width()//2, stats_y - 2))

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
        
    keys = [("v ^", "Selecionar"), ("ENTER", "Jogar"), ("ESC", "Voltar")]
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
