import pygame
import sys
import os

# Same setup as main.py
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
pygame.init()
screen = pygame.display.set_mode((480, 528))

TILE_SIZE, COLS, ROWS = 40, 12, 12
WIDTH = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE
MAGENTA = (255, 0, 255)

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

char_sprites = {}
MAN_RIGHT_BASE = 9
MAN_LEFT_BASE = 0
MAN_FRAMES_PER_DIR = 9

sheet = load_img("StackAttack2/man.png")
frames = slice_sheet(sheet, 8, 16, TILE_SIZE / 16)
char_sprites["pete"] = frames

board = [[0 for _ in range(COLS)] for _ in range(ROWS)]

def handle_bomb(x, y): pass
def do_post_landing(): pass

def approach(a, b, speed):
    diff = b - a
    if abs(diff) <= speed:
        return b
    return a + speed * (1 if diff > 0 else -1)

class Personagem:
    PW = TILE_SIZE - 8
    PH = TILE_SIZE

    def __init__(self, grid_x, grid_y, char_id):
        self.x = float(grid_x * TILE_SIZE + (TILE_SIZE - self.PW) // 2)
        self.y = float(grid_y * TILE_SIZE)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.char_id = char_id
        self.velocidade = 3.5
        self.gravidade = 0.5
        self.jump_force = -7.5
        self.no_chao = False
        self.estado = "parado"
        self.dir = 1
        self.frame = 0
        self.anim_tick = 0
        self.alive = True
        self.stun_timer = 0
        self.jump_queued = False
        self.push_cooldown = 0
        self.sprites = char_sprites[char_id]
        self.num_frames = len(self.sprites)

    @property
    def grid_x(self):
        return max(0, min(COLS - 1, int((self.x + self.PW / 2) / TILE_SIZE)))

    @property
    def grid_y(self):
        return max(0, min(ROWS - 1, int((self.y + self.PH / 2) / TILE_SIZE)))

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.PW, self.PH)

    def pular(self):
        if self.no_chao and self.alive:
            self.jump_queued = True

    def _proximo_caixa(self, board_ref):
        r = self.rect
        if self.dir == 1:
            probe = pygame.Rect(r.right, r.top, 2, r.height)
        else:
            probe = pygame.Rect(r.left - 2, r.top, 2, r.height)
        for ty in range(max(0, probe.top // TILE_SIZE), min(ROWS - 1, (probe.bottom - 1) // TILE_SIZE) + 1):
            for tx in range(max(0, probe.left // TILE_SIZE), min(COLS - 1, (probe.right - 1) // TILE_SIZE) + 1):
                if board_ref[ty][tx] != 0:
                    tile_r = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if probe.colliderect(tile_r):
                        return tx, ty
        return None

    def _rv(self, br):
        self.no_chao = False
        r = self.rect
        for ty in range(max(0, r.top // TILE_SIZE), min(ROWS - 1, (r.bottom - 1) // TILE_SIZE) + 1):
            for tx in range(max(0, r.left // TILE_SIZE), min(COLS - 1, (r.right - 1) // TILE_SIZE) + 1):
                if br[ty][tx] == 0:
                    continue
                tr = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not r.colliderect(tr):
                    continue
                if self.vel_y > 0:
                    self.y = float(tr.top - self.PH)
                    self.vel_y = 0
                    self.no_chao = True
                elif self.vel_y < 0:
                    self.y = float(tr.bottom)
                    self.vel_y = 0
                return
        if self.y + self.PH >= ROWS * TILE_SIZE:
            self.y = float(ROWS * TILE_SIZE - self.PH)
            self.vel_y = 0
            self.no_chao = True

    def _rh(self, br):
        r = self.rect
        for ty in range(max(0, r.top // TILE_SIZE), min(ROWS - 1, (r.bottom - 1) // TILE_SIZE) + 1):
            for tx in range(max(0, r.left // TILE_SIZE), min(COLS - 1, (r.right - 1) // TILE_SIZE) + 1):
                if br[ty][tx] == 0:
                    continue
                tr = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not r.colliderect(tr):
                    continue
                if self.vel_x > 0:
                    self.x = float(tr.left - self.PW)
                elif self.vel_x < 0:
                    self.x = float(tr.right)
                self.vel_x = 0
                return

    def _empurrar_caixa(self, board_ref, from_x, from_y, to_x):
        crate_type = board_ref[from_y][from_x]
        board_ref[from_y][from_x] = 0
        board_ref[from_y][to_x] = crate_type
        by = from_y
        while by < ROWS - 1 and board_ref[by + 1][to_x] == 0:
            board_ref[by][to_x] = 0
            board_ref[by + 1][to_x] = crate_type
            by += 1

    def _atualizar_anim(self):
        prev = getattr(self, '_last_estado', None)
        if prev != self.estado:
            self.anim_tick = 0
            self._last_estado = self.estado
            if self.estado == "andando":
                self.frame = 1
            elif self.estado == "empurrando":
                self.frame = 0
            elif self.estado == "parado":
                self.frame = 0
            elif self.estado == "stun":
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
            tick_rate = 8

        if self.anim_tick >= tick_rate:
            self.anim_tick = 0
            if self.estado == "andando":
                self.frame = (self.frame % (MAN_FRAMES_PER_DIR - 1)) + 1
            elif self.estado == "empurrando":
                self.frame = (self.frame + 1) % min(4, MAN_FRAMES_PER_DIR)
            elif self.estado == "parado":
                self.frame = 0

    def get_sprite(self):
        if not self.alive:
            return self.sprites[min(self.num_frames - 1, self.num_frames - 1)]
        base = MAN_RIGHT_BASE if self.dir == 1 else MAN_LEFT_BASE
        if self.estado == "pulando":
            idx = base + 4
            return self.sprites[min(idx, self.num_frames - 1)]
        if self.estado == "stun":
            idx = base + 7
            return self.sprites[min(idx, self.num_frames - 1)]
        if self.estado == "empurrando":
            idx = base + 3
            return self.sprites[min(idx, self.num_frames - 1)]
        idx = base + (self.frame % MAN_FRAMES_PER_DIR)
        return self.sprites[min(idx, self.num_frames - 1)]

    def atualizar(self, teclas, br):
        if not self.alive:
            return
        if self.stun_timer > 0:
            self.stun_timer -= 1
            self.estado = "stun"
            self.vel_x = 0
            self.vel_y += self.gravidade
            self.x += self.vel_x
            self._rh(br)
            self.y += self.vel_y
            self._rv(br)
            if self.x < 0:
                self.x = 0
            if self.x + self.PW > WIDTH:
                self.x = float(WIDTH - self.PW)
            self._atualizar_anim()
            return

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

        prox = self._proximo_caixa(br) if self.vel_x != 0 else None
        can_push = (prox is not None and self.push_cooldown <= 0)
        if can_push:
            self.estado = "empurrando"
            bx, by = prox
            nnx = bx + self.dir
            if 0 <= nnx < COLS and br[by][nnx] == 0:
                self._empurrar_caixa(br, bx, by, nnx)
                self.push_cooldown = 12
        elif self.vel_x != 0 and self.no_chao:
            self.estado = "andando"
        elif self.vel_x == 0 and self.no_chao:
            self.estado = "parado"

        if self.push_cooldown > 0:
            self.push_cooldown -= 1

        if self.jump_queued and self.no_chao:
            self.vel_y = self.jump_force
            self.no_chao = False
            self.estado = "pulando"
            self.jump_queued = False

        self.vel_y += self.gravidade
        self.x += self.vel_x
        self._rh(br)
        self.y += self.vel_y
        self._rv(br)
        if self.x < 0:
            self.x = 0
        if self.x + self.PW > WIDTH:
            self.x = float(WIDTH - self.PW)
        self._atualizar_anim()


# RUN TESTS
p = Personagem(5, ROWS - 1, "pete")
print("=== SETTLE ===")
for i in range(10):
    p.atualizar({"esquerda": False, "direita": False}, board)
    print("  f%02d: estado=%-10s frame=%d no_chao=%s y=%.1f" % (i, p.estado, p.frame, p.no_chao, p.y))

print("\n=== WALK RIGHT (and check sprite indices) ===")
for i in range(40):
    p.atualizar({"esquerda": False, "direita": True}, board)
    spr = p.get_sprite()
    idx = p.sprites.index(spr)
    if i < 20:
        print("  f%02d: estado=%-10s frame=%d sprite_idx=%d dir=%d" % (i, p.estado, p.frame, idx, p.dir))

print("\n=== WALK LEFT ===")
p2 = Personagem(5, ROWS - 1, "pete")
for i in range(5):
    p2.atualizar({"esquerda": False, "direita": False}, board)
for i in range(20):
    p2.atualizar({"esquerda": True, "direita": False}, board)
    spr = p2.get_sprite()
    idx = p2.sprites.index(spr)
    if i < 10:
        print("  f%02d: estado=%-10s frame=%d sprite_idx=%d dir=%d" % (i, p2.estado, p2.frame, idx, p2.dir))

print("\n=== JUMP ===")
p3 = Personagem(5, ROWS - 1, "pete")
for i in range(5):
    p3.atualizar({"esquerda": False, "direita": False}, board)
p3.pular()
for i in range(20):
    p3.atualizar({"esquerda": False, "direita": False}, board)
    spr = p3.get_sprite()
    idx = p3.sprites.index(spr)
    if i < 15:
        print("  f%02d: estado=%-10s frame=%d sprite_idx=%d dir=%d y=%.1f" % (i, p3.estado, p3.frame, idx, p3.dir, p3.y))

print("\n=== PUSH BOX (box at col 6) ===")
board2 = [[0 for _ in range(COLS)] for _ in range(ROWS)]
board2[ROWS - 1][6] = 1
p4 = Personagem(5, ROWS - 1, "pete")
for i in range(5):
    p4.atualizar({"esquerda": False, "direita": False}, board2)
for i in range(80):
    p4.atualizar({"esquerda": False, "direita": True}, board2)
    if i < 30:
        print("  f%02d: estado=%-10s x=%.1f gx=%d box6=%d box7=%d" % (i, p4.estado, p4.x, p4.grid_x, board2[ROWS-1][6], board2[ROWS-1][7]))

pygame.quit()
print("\nALL DONE")
