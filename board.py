"""
Stack Attack Reborn — Board Logic

Grid manipulation: occupancy checks, gravity, line/match detection,
bomb handling, and post-landing combo logic.
"""
import math
import pygame
from constants import (
    COLS, ROWS, TILE_SIZE, BOMB_TYPE, SAM_BOMB_TYPE, POWERUP_HELMET_TYPE,
    INITIAL_SPAWN_MS, SPAWN_EVENT,
)
from audio import (
    play_sound, sound_land, sound_explode, sound_line_clear, sound_combo,
    sound_game_over_sfx, play_music, update_gameplay_music,
    stop_gameplay_music,
)
from animations import add_particles
import state


# ---------------------------------------------------------------------------
# Occupancy
# ---------------------------------------------------------------------------
def is_cell_occupied(x, y):
    """Check if a grid cell is occupied by a static crate, falling crate, or push animation."""
    if not (0 <= x < COLS and 0 <= y < ROWS):
        return True
    if state.board[y][x] != 0:
        return True
    for fb in state.falling_boxes:
        if fb["x"] == x and fb["y"] == y:
            return True
    for pa in state.push_animations:
        if pa["x"] == x and pa["y"] == y:
            return True
    return False


# ---------------------------------------------------------------------------
# Board gravity (column compaction)
# ---------------------------------------------------------------------------
def apply_board_gravity():
    for x in range(COLS):
        write_y = ROWS - 1
        for y in range(ROWS - 1, -1, -1):
            if state.board[y][x] != 0:
                if write_y != y:
                    state.board[write_y][x] = state.board[y][x]
                    state.helmet_timers[write_y][x] = state.helmet_timers[y][x]
                    state.bomb_timers[write_y][x] = state.bomb_timers[y][x]
                    state.board[y][x] = 0
                    state.helmet_timers[y][x] = 0
                    state.bomb_timers[y][x] = 0
                write_y -= 1


# ---------------------------------------------------------------------------
# Line matching (match-3)
# ---------------------------------------------------------------------------
def find_line_matches():
    matched = set()
    for y in range(ROWS):
        x = 0
        while x < COLS:
            t = state.board[y][x]
            if t == 0 or t == BOMB_TYPE:
                x += 1
                continue
            run = 1
            while x + run < COLS and state.board[y][x + run] == t:
                run += 1
            if run >= 3:
                for i in range(x, x + run):
                    matched.add((i, y))
            x += run
    for x in range(COLS):
        y = 0
        while y < ROWS:
            t = state.board[y][x]
            if t == 0 or t == BOMB_TYPE:
                y += 1
                continue
            run = 1
            while y + run < ROWS and state.board[y + run][x] == t:
                run += 1
            if run >= 3:
                for i in range(y, y + run):
                    matched.add((x, i))
            y += run
    return matched


# ---------------------------------------------------------------------------
# Post-landing: line clears + match combos
# ---------------------------------------------------------------------------
def do_post_landing():
    to_explode = set()

    # Full line clears
    cleared = 0
    for y in range(ROWS):
        if all(state.board[y][x] != 0 for x in range(COLS)):
            cleared += 1
            for x in range(COLS):
                to_explode.add((x, y))

    if cleared > 0:
        state.score += 100 * cleared
        state.difficulty = float(state.selected_level) + math.log10(1 + state.score / 50.0) * 3.0
        state.spawn_interval = max(600, int(INITIAL_SPAWN_MS / state.difficulty))
        pygame.time.set_timer(SPAWN_EVENT, state.spawn_interval)
        state.line_clear_flash = 15
        play_sound(sound_line_clear)
        update_gameplay_music()

        state.screen_shake = 15
        for mx, my in to_explode:
            add_particles(mx * TILE_SIZE, my * TILE_SIZE, (255, 255, 255), 15)

    # Match-3 combos
    matched = find_line_matches()
    if matched:
        state.combo_count += 1
        state.score += 50 * state.combo_count
        to_explode.update(matched)
        play_sound(sound_combo)
        for mx, my in matched:
            add_particles(mx * TILE_SIZE, my * TILE_SIZE, (255, 200, 50), 10)
            
        # Passive: Sam restores 1 bomb when completing colors (Match-3)
        if state.player and state.player.char_id == "sam":
            if state.player.bombs_left < 3:
                state.player.bombs_left += 1
        
        # Passive: Cath's "Sobrecarga" (Color Clear)
        # Destroy all other crates of the same color that was matched
        if state.player and state.player.char_id == "cath":
            matched_colors = set()
            for mx, my in matched:
                ctype = state.board[my][mx]
                if ctype > 0 and ctype not in (POWERUP_HELMET_TYPE, BOMB_TYPE, SAM_BOMB_TYPE):
                    matched_colors.add(ctype)
            
            if matched_colors:
                from audio import sound_explode
                play_sound(sound_explode)
                state.screen_shake = max(state.screen_shake, 12)
                for by in range(ROWS):
                    for bx in range(COLS):
                        if state.board[by][bx] in matched_colors:
                            if (bx, by) not in to_explode:
                                to_explode.add((bx, by))
                                add_particles(bx * TILE_SIZE + TILE_SIZE//2, by * TILE_SIZE + TILE_SIZE//2, (255, 100, 255), 10)

    if to_explode:
        state.explosion_anim_cells = list(to_explode)
        state.explosion_anim_timer = 20
        for mx, my in to_explode:
            state.board[my][mx] = 0
            state.helmet_timers[my][mx] = 0
            state.bomb_timers[my][mx] = 0


# ---------------------------------------------------------------------------
# Bomb explosion
# ---------------------------------------------------------------------------
def handle_bomb(bx, by, is_sam_bomb=False):
    state.screen_shake = 20
    state.explosion_anim_cells = []
    play_sound(sound_explode)
    
    # Sam has a 3x3 bomb radius (radius=1)
    radius = 1
    
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            nx, ny = bx + dx, by + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                state.board[ny][nx] = 0
                state.bomb_timers[ny][nx] = 0
                state.explosion_anim_cells.append((nx, ny))
    state.explosion_anim_timer = 20

    p = state.player
    if p and p.alive and (p.helmet_timer > 0 or (p.char_id == "sam" and is_sam_bomb)):
        pass  # helmet or Sam's passive protects against his own bombs
    elif p and p.alive:
        pgx, pgy = p.grid_x, p.grid_y
        p_row_top = p.grid_y
        p_row_bot = p.grid_y + 1
        in_x_range = abs(pgx - bx) <= radius
        in_y_range = (abs(p_row_top - by) <= radius) or (abs(p_row_bot - by) <= radius)
        if in_x_range and in_y_range:
            p.alive = False
            from game import stop_timers
            stop_timers()
            stop_gameplay_music()
            play_sound(sound_game_over_sfx)
            play_music("gameover.mid")
            return
    state.score += 30


# ---------------------------------------------------------------------------
# Gravity tick (called from GRAVITY_EVENT)
# ---------------------------------------------------------------------------
def handle_gravity():
    p = state.player
    if not p or not p.alive:
        return

    for box in state.falling_boxes[:]:
        landed = False
        if box["y"] == ROWS - 1:
            landed = True
        elif box["y"] + 1 < ROWS:
            if state.board[box["y"] + 1][box["x"]] != 0:
                landed = True
            else:
                for pa in state.push_animations:
                    if pa["x"] == box["x"] and pa["y"] == box["y"] + 1:
                        landed = True
                        break

        if landed:
            bx_pos, by_pos, btype = box["x"], box["y"], box["type"]
            state.board[by_pos][bx_pos] = btype
            if btype == POWERUP_HELMET_TYPE:
                state.helmet_timers[by_pos][bx_pos] = 180
            elif btype == BOMB_TYPE:
                state.bomb_timers[by_pos][bx_pos] = 180
            state.falling_boxes.remove(box)
            play_sound(sound_land)
            state.screen_shake = max(state.screen_shake, 3)
            pgx, pgy = p.grid_x, p.grid_y
            if pgx == bx_pos and pgy == by_pos:
                p.ativar_stun(15)
            if btype == BOMB_TYPE or btype == SAM_BOMB_TYPE:
                handle_bomb(bx_pos, by_pos, is_sam_bomb=(btype == SAM_BOMB_TYPE))
            else:
                state.combo_count = 0
                do_post_landing()
        else:
            box["y"] += 1
