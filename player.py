"""
Stack Attack Reborn — Player Character (Personagem)

Movement, physics, collision resolution, pushing, jumping, and animation.
"""
import pygame
from constants import (
    TILE_SIZE, COLS, ROWS, WIDTH,
    IDLE_FRAMES, WALK_RIGHT_FRAMES, WALK_LEFT_FRAMES,
    PUSH_RIGHT_FRAMES, PUSH_LEFT_FRAMES,
    JUMP_RIGHT_FRAME, JUMP_LEFT_FRAME, STUN_FRAME, STUN_FRAMES,
    JUMP_BUFFER_FRAMES, COYOTE_FRAMES, PUSH_HORIZONTAL_SPEED,
    CHAR_DEFS, BOMB_TYPE, POWERUP_HELMET_TYPE,
)
from assets_loader import char_sprites
from audio import (
    play_sound, play_music,
    sound_jump, sound_super_jump, sound_stun, sound_push, sound_explode,
    sound_powerup, sound_helmet, sound_game_over_sfx,
    stop_gameplay_music,
)
from animations import add_particles, register_push_animation
from board import is_cell_occupied
from highscores import highscores, save_highscores
import state


class Personagem:
    PW = TILE_SIZE - 12  # Reduced width (28px) for easier navigation in 1-tile gaps
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
        self.max_bombs = cdef.get("bombs", 0)
        self.bombs_left = self.max_bombs
        self.no_chao = False
        self.estado = "parado"
        self.dir = 1
        self.frame = 0
        self.anim_tick = 0
        self.alive = True
        self.jump_queued = False
        self.jump_buffer = 0
        self.coyote_timer = 0
        self.stun_timer = 0
        self.push_cooldown = 0
        self.bomb_cooldown = 0
        self.helmet_timer = 0
        self.helmet_charges = 3 if self.char_id == "cath" else 0
        self.max_helmet_charges = 5
        self.has_double_jumped = False
        self.sprites = char_sprites[char_id]
        self.num_frames = len(self.sprites)

    # ----- Properties -----
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

    # ----- Actions -----
    def pular(self):
        if self.alive:
            self.jump_queued = True
            self.jump_buffer = JUMP_BUFFER_FRAMES
            play_sound(sound_jump)



    # ----- Crate detection -----
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
        for box in state.falling_boxes:
            bpx = box.get("px", box["x"] * TILE_SIZE)
            bpy = box.get("py", box["y"] * TILE_SIZE)
            tile_r = pygame.Rect(bpx, bpy, TILE_SIZE, TILE_SIZE)
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
        if is_cell_occupied(dst_x, box_y):
            return False
        if box_y > 0 and board_ref[box_y - 1][box_x] != 0:
            return False
        return True

    # ----- Main update -----
    def atualizar(self, teclas, board_ref):
        if not self.alive:
            return

        if self.stun_timer > 0:
            self.stun_timer -= 1
            self.estado = "stun"
            self.vel_x = 0
            self._atualizar_anim() # Update animation frames during stun
            self._aplicar_fisica(board_ref)
            return



        if self.no_chao:
            self.coyote_timer = COYOTE_FRAMES
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        if self.jump_buffer > 0:
            self.jump_buffer -= 1
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1
        if self.helmet_timer > 0:
            self.helmet_timer -= 1.0 / 60.0

        if self.push_cooldown > 0:
            moving_forward = (self.dir == -1 and teclas.get("esquerda")) or (self.dir == 1 and teclas.get("direita"))
            moving_backward = (self.dir == -1 and teclas.get("direita")) or (self.dir == 1 and teclas.get("esquerda"))
            if moving_forward:
                self.vel_x = PUSH_HORIZONTAL_SPEED * self.dir
                self.estado = "empurrando"
            elif moving_backward:
                self.push_cooldown = 0
                self.vel_x = -self.velocidade if self.dir == 1 else self.velocidade
                self.dir = -self.dir
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
                    
                    # Helmet collection from the side
                    if board_ref[by][bx] == POWERUP_HELMET_TYPE:
                        # Cath doesn't get the timer, only charges
                        if self.char_id == "cath":
                            self.helmet_charges = min(self.max_helmet_charges, self.helmet_charges + 1)
                        else:
                            duration = 10.0 if self.char_id == "sam" else 5.0
                            self.helmet_timer += duration
                        board_ref[by][bx] = 0
                        state.score += 50
                        play_sound(sound_helmet)
                        state.screen_shake = 10
                        add_particles(self.x + self.PW / 2, self.y + self.PH / 2, (100, 255, 100), 20)
                        pushed = False
                        wants_to_push = False # Convert to normal movement since crate is gone
                    
                    if wants_to_push:
                        can_push_single = self._pode_empurrar_para(board_ref, bx, by)
                        
                        # Frank's Passive: Chain Push (push up to 2 boxes)
                        if not can_push_single and self.char_id == "frank":
                            nx2 = bx + self.dir
                            if 0 <= nx2 < COLS and board_ref[by][nx2] != 0:
                                # If blocked by exactly ONE box, check if THAT box can move
                                if self._pode_empurrar_para(board_ref, nx2, by):
                                    self._empurrar_caixa(board_ref, nx2, by, nx2 + self.dir)
                                    self._empurrar_caixa(board_ref, bx, by, nx2)
                                    self.push_cooldown = 24
                                    pushed = True
                                    
                        if not pushed and can_push_single:
                            self._empurrar_caixa(board_ref, bx, by, bx + self.dir)
                            self.push_cooldown = 20
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
                            if board_ref[ty][nnx] != 0:
                                can_push_f = False
                        if can_push_f and not any(
                            b["x"] == nnx and abs(b["py"] - box["py"]) < TILE_SIZE
                            for b in state.falling_boxes
                        ):
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
        if self.jump_buffer > 0:
            if can_jump_from_ground:
                self.vel_y = self.jump_force
                self.no_chao = False
                self.coyote_timer = 0
                self.estado = "pulando"
                self.jump_queued = False
                self.jump_buffer = 0


        self._aplicar_fisica(board_ref)

    # ----- Physics -----
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
                    if board_ref[ty][tx] == POWERUP_HELMET_TYPE:
                        duration = 10.0 if self.char_id == "sam" else 5.0
                        self.helmet_timer += duration
                        board_ref[ty][tx] = 0
                        state.score += 50
                        play_sound(sound_helmet)
                        state.screen_shake = 10
                        add_particles(self.x + self.PW / 2, self.y + self.PH / 2, (100, 255, 100), 20)
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
        r = self.rect
        for box in state.falling_boxes:
            bpx = box.get("px", box["x"] * TILE_SIZE)
            bpy = box.get("py", box["y"] * TILE_SIZE)
            tile_r = pygame.Rect(bpx, bpy, TILE_SIZE, TILE_SIZE)
            if not r.colliderect(tile_r):
                continue
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

        # Check boxes in push animations horizontally
        for anim in state.push_animations:
            tile_r = pygame.Rect(anim["px"], anim["py"], TILE_SIZE, TILE_SIZE)
            if not r.colliderect(tile_r):
                continue
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
                    if self.char_id == "cath":
                        self.helmet_charges = min(self.max_helmet_charges, self.helmet_charges + 1)
                    else:
                        duration = 10.0 if self.char_id == "sam" else 5.0
                        self.helmet_timer += duration
                    board_ref[ty][tx] = 0
                    state.score += 50
                    play_sound(sound_helmet)
                    continue
                if self.vel_y > 0:
                    self.y = float(tile_r.top - self.PH)
                    self.vel_y = 0
                    self.no_chao = True
                elif self.vel_y < 0:
                    # Headbutt Logic (Helmet timer OR Cath's Passive Charges)
                    can_headbutt = self.helmet_timer > 0 or (self.char_id == "cath" and self.helmet_charges > 0)
                    if can_headbutt:
                        # Destroy crate from below
                        board_ref[ty][tx] = 0
                        play_sound(sound_explode)
                        add_particles(tile_r.centerx, tile_r.centery, (200, 200, 200), 12)
                        
                        # Consume charge if not using a timed powerup
                        if self.char_id == "cath" and self.helmet_timer <= 0:
                            self.helmet_charges -= 1
                        
                        # Maintain upward momentum (original arcade feel)
                        self.vel_y *= 0.5 
                        continue
                    else:
                        self.y = float(tile_r.bottom)
                        self.vel_y = 0
                return

        # Check boxes in push animations vertically
        for anim in state.push_animations:
            tile_r = pygame.Rect(anim["px"], anim["py"], TILE_SIZE, TILE_SIZE)
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
            self.has_double_jumped = False

    # ----- Push crate -----
    def _empurrar_caixa(self, board_ref, from_x, from_y, to_x):
        crate_type = board_ref[from_y][from_x]
        board_ref[from_y][from_x] = 0
        landing_y = from_y
        while landing_y < ROWS - 1 and board_ref[landing_y + 1][to_x] == 0:
            landing_y += 1
        bt = 0
        if crate_type == BOMB_TYPE:
            bt = state.bomb_timers[from_y][from_x]
            state.bomb_timers[from_y][from_x] = 0
        register_push_animation(from_x, from_y, to_x, landing_y, crate_type, bomb_timer=bt)

    # ----- Animation -----
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
        elif self.estado == "stun":
            tick_rate = 8 # Animation speed for dizzy effect
        else:
            tick_rate = 10

        if self.anim_tick >= tick_rate:
            self.anim_tick = 0
            if self.estado == "andando":
                self.frame = (self.frame + 1) % len(WALK_RIGHT_FRAMES)
            elif self.estado == "empurrando":
                self.frame = (self.frame + 1) % len(PUSH_RIGHT_FRAMES)
            elif self.estado == "stun":
                self.frame = (self.frame + 1) % len(STUN_FRAMES)
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
            idx = STUN_FRAMES[self.frame % len(STUN_FRAMES)]
            return self.sprites[min(idx, self.num_frames - 1)]
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

    # ----- Falling crate collision -----
    def check_falling_collision(self, falling_boxes_list):
        if not self.alive:
            return
        body_left = self.x + 8
        body_right = self.x + self.PW - 8
        body_top = self.y

        for box in falling_boxes_list[:]:
            box_px = box.get("px", box["x"] * TILE_SIZE)
            box_py = box.get("py", box["y"] * TILE_SIZE)
            crate_left = box_px + 4
            crate_right = box_px + TILE_SIZE - 4
            if body_right < crate_left or body_left > crate_right:
                continue
            crate_bottom = box_py + TILE_SIZE
            if crate_bottom < body_top or box_py > body_top + 16:
                continue

            if box["type"] == POWERUP_HELMET_TYPE:
                if self.char_id == "cath":
                    self.helmet_charges = min(self.max_helmet_charges, self.helmet_charges + 1)
                else:
                    # Sam's Passive: Helmet lasts twice as long
                    duration = 10.0 if self.char_id == "sam" else 5.0
                    self.helmet_timer += duration
                state.score += 50
                play_sound(sound_powerup)
                state.screen_shake = 10
                add_particles(box_px + TILE_SIZE / 2, box_py + TILE_SIZE / 2, (100, 255, 100), 20)
                falling_boxes_list.remove(box)
                continue

            stomp_hit = (
                self.vel_y >= 0
                and (self.y + self.PH) <= box_py + 16
                and (self.y + self.PH / 2) < (box_py + TILE_SIZE / 2)
            )
            if stomp_hit:
                falling_boxes_list.remove(box)
                # Cath's Passive: Stomp gives 25 points instead of 10
                state.score += 25 if self.char_id == "cath" else 10
                play_sound(sound_explode)
                self.vel_y = min(self.vel_y, -4)
                continue

            # Cath's Headbutt for falling boxes
            if self.char_id == "cath" and self.helmet_charges > 0 and self.vel_y < 0:
                # Collision check for head hitting the falling box
                head_r = pygame.Rect(self.x + 4, self.y, self.PW - 8, 10)
                box_r = pygame.Rect(box_px, box_py, TILE_SIZE, TILE_SIZE)
                if head_r.colliderect(box_r):
                    falling_boxes_list.remove(box)
                    self.helmet_charges -= 1
                    play_sound(sound_explode)
                    add_particles(box_px + TILE_SIZE / 2, box_py + TILE_SIZE / 2, (220, 220, 220), 12)
                    self.vel_y = 2 # Bounce down slightly to avoid instant second collision
                    continue

            if self.helmet_timer > 0:
                # Original mechanic: Don't explode, just stun and the box lands
                self.stun_timer = 120 # 2 seconds stun as requested
                self.estado = "stun"
                self.frame = 0 # Start animation from beginning
                play_sound(sound_stun)
                
                # Remove from falling and place on board at current grid
                falling_boxes_list.remove(box)
                gx, gy = box["x"], int(box["py"] // TILE_SIZE)
                gy = max(0, min(ROWS - 1, gy))
                
                if state.board[gy][gx] == 0:
                    state.board[gy][gx] = box["type"]
                
                from board import apply_board_gravity, do_post_landing
                apply_board_gravity()
                do_post_landing()
                continue

            # Death
            self.alive = False
            from game import stop_timers
            stop_timers()
            stop_gameplay_music()
            play_sound(sound_game_over_sfx)
            play_music("gameover.mid")
            char_id = self.char_id
            current_hs = highscores.get(char_id, 0)
            if state.score > current_hs:
                highscores[char_id] = state.score
                save_highscores(highscores)
            return

    # ----- Bomb placement -----
    def try_place_bomb(self, board_ref):
        if self.bombs_left > 0 and self.bomb_cooldown <= 0:
            tx = self.grid_x + self.dir
            ty = self.grid_y
            tx = max(0, min(COLS - 1, tx))
            ty = max(0, min(ROWS - 1, ty))
            if tx == self.grid_x:
                return False
            if board_ref[ty][tx] == BOMB_TYPE:
                return False
            else:
                board_ref[ty][tx] = BOMB_TYPE
                state.bomb_timers[ty][tx] = 180
            self.bombs_left -= 1
            self.bomb_cooldown = 40
            from audio import sound_bomb
            play_sound(sound_bomb)
            return True
        return False
