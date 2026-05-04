"""
Stack Attack Reborn — Game Engine

Handles reset, timers, and the main state machine loops.
"""
import pygame
import sys
import random
from constants import (
    COLS, ROWS, INITIAL_SPAWN_MS, GRAVITY_MS, GRAVITY_EVENT, SPAWN_EVENT,
    CHAR_DEFS, NUM_CRATE_TYPES, BOMB_TYPE, POWERUP_HELMET_TYPE,
)
import state
from player import Personagem
from board import handle_gravity, handle_bomb, apply_board_gravity, do_post_landing
from crane import update_crane, queue_crate_spawn
from audio import (
    start_gameplay_music, stop_gameplay_music, stop_music, pause_music, unpause_music,
    play_music, play_sound, sound_menu_select, sound_menu_move,
)
from animations import update_particles, update_box_visuals
from renderer import draw_title, draw_char_select, draw_level_select, draw_game, draw_retro_tv

# Clock reference
clock = pygame.time.Clock()


simulated_keys = {
    pygame.K_LEFT: False, pygame.K_RIGHT: False,
    pygame.K_UP: False, pygame.K_DOWN: False,
    pygame.K_SPACE: False, pygame.K_RETURN: False, pygame.K_ESCAPE: False
}

def get_touch_key(x, y):
    from constants import WIDTH, HEIGHT, HUD_H
    ctrl_y = HEIGHT + HUD_H
    if y < ctrl_y: return None
    import math
    # Sync with modernized renderer values
    d_x, d_y = 90, ctrl_y + 100
    if math.hypot(x - d_x, y - d_y) < 80:
        if x < d_x - 15: return pygame.K_LEFT
        if x > d_x + 15: return pygame.K_RIGHT
        if y < d_y - 15: return pygame.K_UP
        if y > d_y + 15: return pygame.K_DOWN
        return None
    if math.hypot(x - (WIDTH - 55), y - (ctrl_y + 75)) < 35: return pygame.K_SPACE
    if math.hypot(x - (WIDTH - 135), y - (ctrl_y + 115)) < 35: return pygame.K_b
    if abs(x - (WIDTH // 2 + 30)) < 30 and abs(y - (ctrl_y + 160)) < 20: return pygame.K_RETURN
    if abs(x - (WIDTH // 2 - 30)) < 30 and abs(y - (ctrl_y + 160)) < 20: return pygame.K_q # Q for Back to Menu
    return None


def reset_game(start_diff=1.0):
    state.screen_shake = 0
    state.particles = []
    char_id = CHAR_DEFS[state.selected_char]["id"]
    state.board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    state.helmet_timers = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    state.bomb_timers = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    state.player = Personagem(5, ROWS - 1, char_id)
    state.falling_boxes = []
    state.push_animations = []
    state.score = 0
    state.game_state = "play"
    state.cranes = []
    state.crane_frame = 0
    state.difficulty = float(start_diff)
    state.spawn_interval = max(800, int(INITIAL_SPAWN_MS / state.difficulty))
    state.line_clear_flash = 0
    state.combo_count = 0
    state.match_anim_cells = []
    state.match_anim_timer = 0
    pygame.time.set_timer(GRAVITY_EVENT, GRAVITY_MS)
    pygame.time.set_timer(SPAWN_EVENT, state.spawn_interval)
    start_gameplay_music()

def stop_timers():
    pygame.time.set_timer(GRAVITY_EVENT, 0)
    pygame.time.set_timer(SPAWN_EVENT, 0)

def run_game():
    ad_timer = 0
    state.selected_level = 1
    state.game_state = "title"
    play_music("title.mid", loops=-1)

    while True:

        for event in pygame.event.get():
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                k = get_touch_key(*event.pos)
                if k:
                    is_down = (event.type == pygame.MOUSEBUTTONDOWN)
                    simulated_keys[k] = is_down
                    if is_down: pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k))
            pygame.event.post(event)
        events = pygame.event.get()

        if state.game_state == "title":
            draw_title()
            for event in events:
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        play_sound(sound_menu_select)
                        stop_music()
                        state.game_state = "char_select"
                    elif event.key == pygame.K_q: pygame.quit(); sys.exit()
            clock.tick(30)

        elif state.game_state == "char_select":
            draw_char_select()
            for event in events:
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        play_sound(sound_menu_move)
                        state.game_state = "title"
                        play_music("title.mid", loops=-1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        play_sound(sound_menu_select)
                        state.game_state = "level_select"
                    elif event.key == pygame.K_LEFT:
                        state.selected_char = (state.selected_char - 1) % len(CHAR_DEFS)
                        play_sound(sound_menu_move)
                    elif event.key == pygame.K_RIGHT:
                        state.selected_char = (state.selected_char + 1) % len(CHAR_DEFS)
                        play_sound(sound_menu_move)
                    elif event.key == pygame.K_UP:
                        state.selected_char = (state.selected_char - 3) % len(CHAR_DEFS)
                        play_sound(sound_menu_move)
                    elif event.key == pygame.K_DOWN:
                        state.selected_char = (state.selected_char + 3) % len(CHAR_DEFS)
                        play_sound(sound_menu_move)
            clock.tick(30)

        elif state.game_state == "level_select":
            draw_level_select()
            for event in events:
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        play_sound(sound_menu_move)
                        state.game_state = "char_select"
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        play_sound(sound_menu_select)
                        stop_music()
                        reset_game(state.selected_level)
                    elif event.key == pygame.K_UP:
                        state.selected_level = max(1, state.selected_level - 1)
                        play_sound(sound_menu_move)
                    elif event.key == pygame.K_DOWN:
                        state.selected_level = min(3, state.selected_level + 1)
                        play_sound(sound_menu_move)
            clock.tick(30)

        elif state.game_state == "play":
            for event in events:
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if not state.player.alive:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r: reset_game(state.selected_level)
                        elif event.key == pygame.K_q: 
                            state.game_state = "title"
                            play_music("title.mid", loops=-1)
                    continue

                if event.type == SPAWN_EVENT:
                    x = random.randint(0, COLS - 1)
                    r = random.random()
                    # Bomb: 6%, Helmet: 2% (from 0.06 to 0.08)
                    ctype = BOMB_TYPE if r < 0.06 else (POWERUP_HELMET_TYPE if r < 0.08 else random.randint(1, NUM_CRATE_TYPES))
                    queue_crate_spawn(x, ctype)
                if event.type == GRAVITY_EVENT: handle_gravity()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        stop_timers(); pause_music()
                        state.game_state = "pause"
                    elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE): state.player.pular()
                    elif event.key == pygame.K_b: state.player.try_place_bomb(state.board)

            if state.player.alive:
                keys = pygame.key.get_pressed()
                teclas = {"esquerda": keys[pygame.K_LEFT] or keys[pygame.K_a] or simulated_keys.get(pygame.K_LEFT, False), "direita": keys[pygame.K_RIGHT] or keys[pygame.K_d] or simulated_keys.get(pygame.K_RIGHT, False)}
                state.player.atualizar(teclas, state.board)
                state.player.check_falling_collision(state.falling_boxes)
                update_crane()
                update_particles()

            if state.line_clear_flash > 0: state.line_clear_flash -= 1
            if state.explosion_anim_timer > 0:
                state.explosion_anim_timer -= 1
                if state.explosion_anim_timer == 0:
                    state.explosion_anim_cells = []
                    apply_board_gravity(); do_post_landing()

            needs_gravity = False
            for y in range(ROWS):
                for x in range(COLS):
                    if state.board[y][x] == POWERUP_HELMET_TYPE:
                        if state.helmet_timers[y][x] > 0:
                            state.helmet_timers[y][x] -= 1
                            if state.helmet_timers[y][x] <= 0: state.board[y][x] = 0; needs_gravity = True
                    elif state.board[y][x] == BOMB_TYPE:
                        if state.bomb_timers[y][x] > 0:
                            state.bomb_timers[y][x] -= 1
                            if state.bomb_timers[y][x] <= 0: handle_bomb(x, y)
            if needs_gravity: apply_board_gravity(); do_post_landing()
            update_box_visuals(); draw_game()
            clock.tick(60)

        elif state.game_state == "pause":
            draw_game(flip=False); draw_retro_tv("pause")
            for event in events:
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        play_sound(sound_menu_select)
                        state.game_state = "ad"
                        ad_timer = 180
                    elif event.key == pygame.K_q: # Back to Menu from Pause
                        play_sound(sound_menu_move)
                        state.game_state = "title"
                        play_music("title.mid", loops=-1)
            clock.tick(60)

        elif state.game_state == "ad":
            draw_retro_tv("ad", max(0, ad_timer // 60))
            if ad_timer > 0: ad_timer -= 1
            for event in events:
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE) and ad_timer <= 0:
                        play_sound(sound_menu_select); unpause_music()
                        pygame.time.set_timer(GRAVITY_EVENT, GRAVITY_MS)
                        pygame.time.set_timer(SPAWN_EVENT, state.spawn_interval)
                        state.game_state = "play"
            clock.tick(60)
