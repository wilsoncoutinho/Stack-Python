"""
Stack Attack Reborn — Rendering System

Handles all draw_* functions for the game, HUD, and UI screens.
"""
import pygame
import random
import math
from constants import (
    WIDTH, HEIGHT, HUD_H, TILE_SIZE, ROWS, COLS,
    CRANE_Y, POWERUP_HELMET_TYPE, BOMB_TYPE,
    CRANE_FRAME_FOR_CRATE, CRANE_EMPTY_FRAME,
    CHAR_DEFS,
)
from assets_loader import (
    bg_img, title_img, crate_sprites, char_icons,
    crane_sprites, CRANE_SPRITE_W,
    font_big, font_med, font_sm, font_xs,
    render_styled_text, crate_sprite_for_type,
    trophy_icon,
)
from highscores import highscores
import state

# Get screen reference (initialized in main.py or game.py)
_screen = None

def set_screen(surface):
    global _screen
    _screen = surface

def draw_hud_to(target_surf):
    # Background panel
    pygame.draw.rect(target_surf, (18, 22, 32), (0, HEIGHT, WIDTH, HUD_H))
    pygame.draw.line(target_surf, (50, 60, 80), (0, HEIGHT), (WIDTH, HEIGHT), 2)
    
    # Left side: Score
    icon_y = HEIGHT + (HUD_H - trophy_icon.get_height()) // 2
    target_surf.blit(trophy_icon, (10, icon_y))
    
    txt_pts = font_med.render(str(state.score), True, (255, 210, 50))
    target_surf.blit(txt_pts, (15 + trophy_icon.get_width(), HEIGHT + (HUD_H - txt_pts.get_height()) // 2))
    
    # Center: Passive Ability Badge
    if state.player:
        from constants import CHAR_DEFS
        cdef = next(c for c in CHAR_DEFS if c["id"] == state.player.char_id)
        ability = cdef.get("ability", "none")
        
        ability_labels = {
            "none": ("TRABALHADOR", (150, 150, 170)),
            "speed": ("VELOZ", (100, 220, 255)),
            "double_push": ("MAIS FORTE", (255, 180, 80)),
            "high_jump": ("PULO ALTO", (120, 255, 120)),
            "stomp": ("CABEÇADA", (255, 100, 100)),
            "bombs": ("DEMOLIDOR", (255, 50, 50))
        }
        ab_name, ab_color = ability_labels.get(ability, ("???", (255, 255, 255)))
        
        cx = WIDTH // 2
        ab_surf = font_xs.render(ab_name, True, ab_color)
        
        # Dynamic width badge
        bw = max(80, ab_surf.get_width() + 20)
        bg_rect = pygame.Rect(cx - bw//2, HEIGHT + (HUD_H - 24)//2, bw, 24)
        
        # Draw the Badge (dark fill + bright border)
        pygame.draw.rect(target_surf, (ab_color[0]//5, ab_color[1]//5, ab_color[2]//5), bg_rect, border_radius=6)
        pygame.draw.rect(target_surf, ab_color, bg_rect, 1, border_radius=6)
        target_surf.blit(ab_surf, (cx - ab_surf.get_width()//2, HEIGHT + (HUD_H - ab_surf.get_height()) // 2))
        
    # Right side: Level and Bombs
    lvl_txt = font_sm.render(f"NIVEL {int(state.difficulty)}", True, (180, 190, 210))
    target_surf.blit(lvl_txt, (WIDTH - lvl_txt.get_width() - 10, HEIGHT + (HUD_H - lvl_txt.get_height()) // 2))
    
    if state.player and getattr(state.player, "max_bombs", 0) > 0:
        # Sam's Bombs Icon
        bomb_icon = crate_sprite_for_type(BOMB_TYPE)
        icon_small = pygame.transform.scale(bomb_icon, (26, 26))
        target_surf.blit(icon_small, (WIDTH - 100, HEIGHT + 28))
        b_color = (255, 120, 120) if state.player.bombs_left > 0 else (120, 80, 80)
        b_txt = font_sm.render(f"X{state.player.bombs_left}", True, b_color)
        target_surf.blit(b_txt, (WIDTH - 70, HEIGHT + 30))
        
    if state.player and getattr(state.player, "helmet_charges", 0) > 0:
        # Cath's Helmet Icon
        helmet_icon = crate_sprite_for_type(POWERUP_HELMET_TYPE)
        icon_small = pygame.transform.scale(helmet_icon, (26, 26))
        target_surf.blit(icon_small, (WIDTH - 100, HEIGHT + 28))
        c_color = (120, 255, 120)
        c_txt = font_sm.render(f"X{state.player.helmet_charges}", True, c_color)
        target_surf.blit(c_txt, (WIDTH - 70, HEIGHT + 30))
        
    # Overlays
    if state.player and state.player.helmet_timer > 0:
        h_secs = math.ceil(state.player.helmet_timer)
        h_txt = font_sm.render(f"CAPACETE {h_secs}", True, (100, 255, 100))
        target_surf.blit(h_txt, (10, HEIGHT + 32))
        
    if state.combo_count > 1:
        combo_txt = font_sm.render(f"COMBO X{state.combo_count}!", True, (255, 150, 50))
        target_surf.blit(combo_txt, (WIDTH // 2 - combo_txt.get_width() // 2, HEIGHT + 32))

def draw_game(flip=True):
    if not _screen: return
    
    offset_x = 0
    offset_y = 0
    if state.screen_shake > 0:
        offset_x = random.randint(-state.screen_shake, state.screen_shake)
        offset_y = random.randint(-state.screen_shake, state.screen_shake)
        state.screen_shake -= 1

    temp_surface = pygame.Surface((WIDTH, HEIGHT + HUD_H))
    temp_surface.blit(bg_img, (0, 0))

    if state.line_clear_flash > 0:
        flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = int(min(180, state.line_clear_flash * 18))
        flash_surf.fill((255, 255, 255, alpha))
        temp_surface.blit(flash_surf, (0, 0))

    animated_cells = {(anim["x"], anim["y"]) for anim in state.push_animations}
    for y in range(ROWS):
        for x in range(COLS):
            if state.board[y][x] != 0 and (x, y) not in animated_cells:
                if state.board[y][x] == POWERUP_HELMET_TYPE:
                    ht = state.helmet_timers[y][x]
                    if 0 < ht < 60 and (ht // 5) % 2 == 0: continue
                elif state.board[y][x] == BOMB_TYPE:
                    bt = state.bomb_timers[y][x]
                    if 0 < bt < 60 and (bt // 5) % 2 == 0: continue
                
                temp_surface.blit(crate_sprite_for_type(state.board[y][x]), (x * TILE_SIZE, y * TILE_SIZE))
                
                if state.board[y][x] == BOMB_TYPE:
                    spark_x = x * TILE_SIZE + 20
                    spark_y = y * TILE_SIZE - 5
                    if (pygame.time.get_ticks() // 80) % 2 == 0:
                        wx = spark_x + random.randint(-1, 1)
                        wy = spark_y + random.randint(-1, 1)
                        pygame.draw.circle(temp_surface, (255, 220, 100), (wx, wy), random.randint(2, 4))
                        pygame.draw.circle(temp_surface, (255, 255, 255), (wx, wy), 1)

    if state.explosion_anim_timer > 0:
        exp_frame = 10 + (4 - ((state.explosion_anim_timer - 1) // 5) - 1)
        exp_frame = max(10, min(13, exp_frame))
        for mx, my in state.explosion_anim_cells:
            temp_surface.blit(crate_sprites[exp_frame], (mx * TILE_SIZE, my * TILE_SIZE))

    for exp in state.floating_explosions:
        exp_frame = 10 + (4 - ((exp["timer"] - 1) // 5) - 1)
        exp_frame = max(10, min(13, exp_frame))
        temp_surface.blit(crate_sprites[exp_frame], (int(exp["px"]), int(exp["py"])))

    for box in state.falling_boxes:
        bpx = box.get("px", box["x"] * TILE_SIZE)
        bpy = box.get("py", box["y"] * TILE_SIZE)
        temp_surface.blit(crate_sprite_for_type(box["type"]), (int(bpx), int(bpy)))
        if box["type"] == BOMB_TYPE:
            spark_x = int(bpx) + 20
            spark_y = int(bpy) - 5
            if (pygame.time.get_ticks() // 80) % 2 == 0:
                pygame.draw.circle(temp_surface, (255, 220, 100), (spark_x, spark_y), random.randint(2, 4))

    for anim in state.push_animations:
        temp_surface.blit(crate_sprite_for_type(anim["type"]), (int(anim["px"]), int(anim["py"])))

    # Rail
    rail_y = CRANE_Y + 2
    pygame.draw.rect(temp_surface, (100, 70, 50), (0, rail_y, WIDTH, 5))
    pygame.draw.rect(temp_surface, (160, 120, 80), (0, rail_y + 1, WIDTH, 3))

    for c in state.cranes:
        cx = c["x"]
        if cx + CRANE_SPRITE_W < 0 or cx > WIDTH: continue
        frame_idx = CRANE_FRAME_FOR_CRATE.get(c["type"], 0) if not c["dropped"] else CRANE_EMPTY_FRAME
        temp_surface.blit(crane_sprites[min(frame_idx, len(crane_sprites)-1)], (int(cx), CRANE_Y))

    if state.player and state.player.alive:
        sprite = state.player.get_sprite()
        draw_x = state.player.x + (state.player.PW - sprite.get_width()) / 2
        draw_y = state.player.y + state.player.PH - sprite.get_height()
        if not (state.player.estado == "stun" and state.player.stun_timer % 6 < 3):
            temp_surface.blit(sprite, (int(draw_x), int(draw_y)))
    
    for p in state.particles:
        size = max(1, p["life"] // 8)
        pygame.draw.rect(temp_surface, p["color"], (int(p["x"]), int(p["y"]), size, size))

    draw_hud_to(temp_surface)

    if state.player and not state.player.alive:
        overlay = pygame.Surface((WIDTH, HEIGHT + HUD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        temp_surface.blit(overlay, (0, 0))
        panel_w, panel_h = 300, 260
        panel_x = WIDTH // 2 - panel_w // 2
        panel_y = HEIGHT // 2 - panel_h // 2
        pygame.draw.rect(temp_surface, (10, 10, 15), (panel_x + 6, panel_y + 6, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(temp_surface, (35, 40, 55), (panel_x, panel_y, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(temp_surface, (255, 60, 60), (panel_x, panel_y, panel_w, panel_h), width=4, border_radius=20)
        
        t_go = render_styled_text("GAME OVER", font_big, (255, 255, 255), outline_color=(60, 0, 0), outline_width=4, gradient=((255, 100, 100), (180, 20, 20)))
        temp_surface.blit(t_go, (WIDTH // 2 - t_go.get_width() // 2, panel_y + 15))
        
        icon = char_icons[CHAR_DEFS[state.selected_char]["id"]]
        temp_surface.blit(icon, (WIDTH // 2 - icon.get_width() // 2, panel_y + 55))
        
        score_val = font_med.render(str(state.score), True, (255, 255, 255))
        temp_surface.blit(score_val, (WIDTH // 2 - score_val.get_width() // 2, panel_y + 145))
        score_lbl = font_xs.render("PONTOS TOTAIS", True, (140, 150, 170))
        temp_surface.blit(score_lbl, (WIDTH // 2 - score_lbl.get_width() // 2, panel_y + 172))

        char_id = CHAR_DEFS[state.selected_char]["id"]
        best = highscores.get(char_id, 0)
        is_new = state.score >= best and state.score > 0
        hs_msg = "NOVO RECORDE" if is_new else f"RECORDE {best}"
        t_hs = font_sm.render(hs_msg, True, (100, 255, 100) if is_new else (255, 210, 50))
        temp_surface.blit(t_hs, (WIDTH // 2 - t_hs.get_width() // 2, panel_y + 200))
        
        instr = font_sm.render("R REINICIAR   Q SAIR", True, (200, 210, 230))
        temp_surface.blit(instr, (WIDTH // 2 - instr.get_width() // 2, panel_y + 232))

    _screen.fill((0, 0, 0))
    _screen.blit(temp_surface, (offset_x, offset_y))
    if flip: draw_mobile_controls()
    pygame.display.flip()

def draw_retro_tv(content_type="pause", timer=0):
    overlay = pygame.Surface((WIDTH, HEIGHT + HUD_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    _screen.blit(overlay, (0, 0))
    
    tv_w, tv_h = 320, 240
    tv_x, tv_y = WIDTH // 2 - tv_w // 2, (HEIGHT + HUD_H) // 2 - tv_h // 2
    pygame.draw.rect(_screen, (70, 65, 60), (tv_x, tv_y, tv_w, tv_h), border_radius=20)
    pygame.draw.rect(_screen, (30, 25, 20), (tv_x, tv_y, tv_w, tv_h), width=8, border_radius=20)
    
    screen_w, screen_h = 240, 180
    screen_x, screen_y = tv_x + 20, tv_y + 25
    pygame.draw.rect(_screen, (15, 15, 15), (screen_x-4, screen_y-4, screen_w+8, screen_h+8), border_radius=10)
    
    if content_type == "pause":
        for _ in range(150):
            nx, ny = random.randint(screen_x, screen_x + screen_w - 4), random.randint(screen_y, screen_y + screen_h - 4)
            c = random.randint(80, 180)
            pygame.draw.rect(_screen, (c, c, c), (nx, ny, 4, 4))
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            p_txt = font_big.render("PAUSE", True, (0, 255, 0))
            _screen.blit(p_txt, (screen_x + screen_w // 2 - p_txt.get_width() // 2, screen_y + screen_h // 2 - 30))
            
            s_txt = font_sm.render("PRESSIONE 'Q' OU 'SELECT' PARA SAIR", True, (180, 190, 200))
            _screen.blit(s_txt, (screen_x + screen_w // 2 - s_txt.get_width() // 2, screen_y + screen_h // 2 + 30))
    elif content_type == "ad":
        pygame.draw.rect(_screen, (240, 235, 210), (screen_x, screen_y, screen_w, screen_h), border_radius=5)
        ad_title = font_med.render("CRATE COLA", True, (200, 30, 30))
        _screen.blit(ad_title, (screen_x + screen_w // 2 - ad_title.get_width() // 2, screen_y + 20))
        ad_slogan = font_xs.render("Beba e pule alto!", True, (40, 40, 40))
        _screen.blit(ad_slogan, (screen_x + screen_w // 2 - ad_slogan.get_width() // 2, screen_y + 55))
        pygame.draw.rect(_screen, (139, 69, 19), (screen_x + screen_w // 2 - 20, screen_y + 80, 40, 40))
        t_txt = font_xs.render(f"Voltando em {timer}...", True, (80, 80, 80))
        _screen.blit(t_txt, (screen_x + screen_w // 2 - t_txt.get_width() // 2, screen_y + 140))

    for row in range(screen_y, screen_y + screen_h, 4):
        s = pygame.Surface((screen_w, 2), pygame.SRCALPHA)
        s.fill((0, 0, 0, 80))
        _screen.blit(s, (screen_x, row))
    
    draw_mobile_controls()

    
    pygame.display.flip()


def draw_mobile_controls():
    if not _screen: return
    try:
        from constants import CONTROLS_H
    except ImportError:
        return
    ctrl_y = HEIGHT + HUD_H
    
    # Base Gameboy Chassis (slightly lighter, modern off-white)
    chassis_color = (225, 230, 220)
    pygame.draw.rect(_screen, chassis_color, (0, ctrl_y, WIDTH, CONTROLS_H))
    
    # Top bevel highlight and shadow
    pygame.draw.line(_screen, (180, 185, 175), (0, ctrl_y), (WIDTH, ctrl_y), 4)
    pygame.draw.line(_screen, (255, 255, 255), (0, ctrl_y+4), (WIDTH, ctrl_y+4), 2)
    
    # Modern Rounded D-Pad
    d_x, d_y = 90, ctrl_y + 100
    d_w, d_h = 40, 40
    d_color = (45, 48, 52)
    d_shadow = (180, 185, 175)
    
    # D-pad shadow
    pygame.draw.rect(_screen, d_shadow, (d_x - d_w//2 - 5, d_y - d_h*1.5 - 5, d_w + 10, d_h*3 + 10), border_radius=12)
    pygame.draw.rect(_screen, d_shadow, (d_x - d_w*1.5 - 5, d_y - d_h//2 - 5, d_w*3 + 10, d_h + 10), border_radius=12)
    
    # D-pad cross (Vertical then Horizontal to blend)
    pygame.draw.rect(_screen, d_color, (d_x - d_w//2, d_y - d_h*1.5, d_w, d_h*3), border_radius=8)
    pygame.draw.rect(_screen, d_color, (d_x - d_w*1.5, d_y - d_h//2, d_w*3, d_h), border_radius=8)
    
    # Center circle for D-pad indentation
    pygame.draw.circle(_screen, (35, 38, 42), (d_x, d_y), 12)
    
    # Modern A / B Buttons
    btn_r = 28
    a_x, a_y = WIDTH - 55, ctrl_y + 75
    b_x, b_y = WIDTH - 135, ctrl_y + 115
    
    btn_color = (210, 45, 75)
    btn_shadow = (180, 185, 175)
    btn_highlight = (240, 80, 100)
    
    # Shadows
    pygame.draw.circle(_screen, btn_shadow, (a_x + 2, a_y + 4), btn_r + 2)
    pygame.draw.circle(_screen, btn_shadow, (b_x + 2, b_y + 4), btn_r + 2)
    
    # Base buttons
    pygame.draw.circle(_screen, btn_color, (a_x, a_y), btn_r)
    pygame.draw.circle(_screen, btn_color, (b_x, b_y), btn_r)
    
    # Inner highlight (top left)
    pygame.draw.arc(_screen, btn_highlight, (a_x - btn_r + 4, a_y - btn_r + 4, btn_r*2 - 8, btn_r*2 - 8), 1.5, 3.14, 4)
    pygame.draw.arc(_screen, btn_highlight, (b_x - btn_r + 4, b_y - btn_r + 4, btn_r*2 - 8, btn_r*2 - 8), 1.5, 3.14, 4)
    
    a_txt = font_sm.render("A", True, (255, 200, 210))
    _screen.blit(a_txt, (a_x - a_txt.get_width()//2 + 1, a_y - a_txt.get_height()//2 + 2))
    
    b_txt = font_sm.render("B", True, (255, 200, 210))
    _screen.blit(b_txt, (b_x - b_txt.get_width()//2 + 1, b_y - b_txt.get_height()//2 + 2))
    
    # Start / Select (Pill shaped, angled look via offset)
    st_w, st_h = 45, 14
    st_x, st_y = WIDTH // 2 + 30, ctrl_y + 160
    se_x, se_y = WIDTH // 2 - 30, ctrl_y + 160
    
    st_color = (80, 85, 90)
    pygame.draw.rect(_screen, d_shadow, (st_x - st_w//2 + 2, st_y - st_h//2 + 3, st_w, st_h), border_radius=7)
    pygame.draw.rect(_screen, d_shadow, (se_x - st_w//2 + 2, se_y - st_h//2 + 3, st_w, st_h), border_radius=7)
    
    pygame.draw.rect(_screen, st_color, (st_x - st_w//2, st_y - st_h//2, st_w, st_h), border_radius=7)
    pygame.draw.rect(_screen, st_color, (se_x - st_w//2, se_y - st_h//2, st_w, st_h), border_radius=7)
    
    # Labels for Start/Select
    lbl_sel = font_xs.render("SAIR", True, (140, 145, 140))
    lbl_st = font_xs.render("START", True, (140, 145, 140))
    _screen.blit(lbl_sel, (se_x - lbl_sel.get_width()//2, se_y - 20))
    _screen.blit(lbl_st, (st_x - lbl_st.get_width()//2, st_y - 20))


def draw_title():
    _screen.blit(title_img, (0, 0))
    pulse = int(128 + 127 * abs((pygame.time.get_ticks() % 2000) / 1000 - 1))
    t = font_med.render("Pressione ENTER para jogar", True, (pulse, pulse, 255))
    _screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT + HUD_H - 36))
    draw_mobile_controls()

    pygame.display.flip()

def draw_char_select():
    total_h = HEIGHT + HUD_H
    _screen.fill((18, 22, 32))
    
    # Background grid pattern
    for i in range(0, WIDTH, 40):
        pygame.draw.line(_screen, (25, 30, 45), (i, 0), (i, total_h))
    for j in range(0, total_h, 40):
        pygame.draw.line(_screen, (25, 30, 45), (0, j), (WIDTH, j))

    title_y = 15
    t_surf = render_styled_text("SELECIONE O PERSONAGEM", font_big, (255, 255, 255), 
                                outline_color=(10, 20, 50), outline_width=3, 
                                gradient=((255, 255, 255), (180, 200, 255)))
    _screen.blit(t_surf, (WIDTH // 2 - t_surf.get_width() // 2, title_y))
    
    pygame.draw.line(_screen, (255, 210, 50), (40, title_y + 45), (WIDTH - 40, title_y + 45), 3)

    margin_x, margin_y, spacing_x, spacing_y = 20, 85, 12, 12
    cell_w = (WIDTH - (margin_x * 2) - 2 * spacing_x) // 3
    cell_h = (total_h - margin_y - 65 - spacing_y) // 2

    for i, cdef in enumerate(CHAR_DEFS):
        r, c = i // 3, i % 3
        is_sel = (i == state.selected_char)
        rx, ry = margin_x + c * (cell_w + spacing_x), margin_y + r * (cell_h + spacing_y)
        cx = rx + cell_w // 2
        
        if is_sel:
            ry -= int(5 * abs(math.sin(pygame.time.get_ticks() * 0.005)))

        rect = pygame.Rect(rx, ry, cell_w, cell_h)

        if is_sel:
            for thickness in range(1, 5):
                alpha = 150 // thickness
                s = pygame.Surface((cell_w + thickness*2, cell_h + thickness*2), pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 210, 50, alpha), s.get_rect(), border_radius=12, width=1)
                _screen.blit(s, (rx - thickness, ry - thickness))
            
        pygame.draw.rect(_screen, (45, 52, 70) if is_sel else (32, 36, 48), rect, border_radius=10)
        pygame.draw.rect(_screen, (255, 210, 50) if is_sel else (60, 65, 80), rect, 3 if is_sel else 1, border_radius=10)

        if is_sel:
            tag_w, tag_h = 76, 20
            pygame.draw.rect(_screen, (255, 210, 50), (cx - tag_w//2, ry - 10, tag_w, tag_h), border_radius=5)
            tag_txt = font_xs.render("EQUIPADO", True, (20, 20, 25))
            _screen.blit(tag_txt, (cx - tag_txt.get_width()//2, ry - 8))

        # Sprite
        from assets_loader import char_sprites
        sprites = char_sprites[cdef["id"]]
        if sprites:
            char_spr = sprites[0]
            spr_h = int(cell_h * 0.35)
            spr_w = int(spr_h * char_spr.get_width() / char_spr.get_height())
            scaled_spr = pygame.transform.scale(char_spr, (spr_w, spr_h))
            pygame.draw.ellipse(_screen, (0, 0, 0, 130), (cx - 15, ry + 15 + spr_h - 4, 30, 7))
            _screen.blit(scaled_spr, (cx - spr_w // 2, ry + 15))
            sprite_bottom = ry + 15 + spr_h

        # Name & Record
        name_str = cdef["name"].upper().replace("-", " ")
        name_parts = name_str.split()
        if len(name_parts) == 3: name_parts = [name_parts[0] + " " + name_parts[1], name_parts[2]]
        
        name_y = sprite_bottom + 4
        for part in name_parts:
            p_font = font_xs if len(part) > 9 else font_sm
            p_surf = render_styled_text(part, p_font, (255, 255, 255) if is_sel else (180, 190, 200), outline_color=(0, 0, 0), outline_width=2)
            _screen.blit(p_surf, (cx - p_surf.get_width() // 2, name_y))
            name_y += 14 if p_font == font_xs else 16
        
        rec = highscores.get(cdef["id"], 0)
        rec_surf = render_styled_text(f"RECORDE {rec}", font_xs, (255, 210, 50) if rec > 0 else (120, 130, 145), outline_width=1)
        # Give a small gap before the record
        _screen.blit(rec_surf, (cx - rec_surf.get_width() // 2, name_y + 2))
        name_y += 14

        # Stats & Passive
        # Move the speed bar and passive section a bit further down to clear the names
        bar_y, bar_w, bar_x = name_y + 10, cell_w - 55, rx + 38
        
        # Speed 
        pygame.draw.rect(_screen, (22, 24, 32), (bar_x, bar_y, bar_w, 7), border_radius=3)
        pygame.draw.rect(_screen, (70, 150, 255), (bar_x, bar_y, int(bar_w * (cdef['speed'] / 5.0)), 7), border_radius=3)
        spd_txt = font_xs.render("VEL", True, (70, 150, 255))
        _screen.blit(spd_txt, (rx + 8, bar_y - 2))
        
        # Passive Badge
        ability = cdef.get("ability", "none")
        ability_labels = {
            "none": ("TRABALHADOR", (150, 150, 170)),
            "speed": ("VELOZ", (100, 220, 255)),
            "double_push": ("MAIS FORTE", (255, 180, 80)),
            "high_jump": ("PULO ALTO", (120, 255, 120)),
            "stomp": ("CABEÇADA", (255, 100, 100)),
            "bombs": ("DEMOLIDOR", (255, 50, 50))
        }
        
        ab_name, ab_color = ability_labels.get(ability, ("???", (255, 255, 255)))
        
        # Draw the colored badge (centered below the velocity bar)
        badge_w, badge_h = cell_w - 20, 22
        badge_rect = pygame.Rect(cx - badge_w//2, bar_y + 16, badge_w, badge_h)
        pygame.draw.rect(_screen, (ab_color[0]//5, ab_color[1]//5, ab_color[2]//5), badge_rect, border_radius=6)
        pygame.draw.rect(_screen, ab_color, badge_rect, 1, border_radius=6)
        
        ab_surf = font_xs.render(ab_name, True, ab_color)
        _screen.blit(ab_surf, (badge_rect.centerx - ab_surf.get_width()//2, badge_rect.centery - ab_surf.get_height()//2))
    # Footer navigation bar
    footer_y = total_h - 45
    pygame.draw.rect(_screen, (15, 18, 25), (0, footer_y, WIDTH, 45))
    pygame.draw.line(_screen, (50, 55, 75), (0, footer_y), (WIDTH, footer_y), 2)
    
    instr = [("SETAS", "Navegar"), ("ENTER", "Jogar"), ("ESC", "Sair")]
    total_instr_w = sum(font_sm.size(k)[0] + font_sm.size(f" {t}    ")[0] for k, t in instr)
    ix = (WIDTH - total_instr_w) // 2
    for key, txt in instr:
        k_r = font_sm.render(key, True, (255, 210, 50))
        t_r = font_sm.render(f" {txt}    ", True, (210, 215, 230))
        _screen.blit(k_r, (ix, footer_y + 12))
        ix += k_r.get_width()
        _screen.blit(t_r, (ix, footer_y + 12))
        ix += t_r.get_width()

    draw_mobile_controls()


    pygame.display.flip()

def draw_level_select():
    total_h = HEIGHT + HUD_H

    # Gradient background with scanlines
    for y_line in range(total_h):
        t = y_line / total_h
        r = int(25 + 10 * t)
        g = int(30 + 15 * t)
        b = int(45 + 20 * t)
        if (y_line // 3) % 2 == 0:
            r = max(0, r - 5); g = max(0, g - 5); b = max(0, b - 5)
        pygame.draw.line(_screen, (r, g, b), (0, y_line), (WIDTH, y_line))

    # Header bar
    pygame.draw.rect(_screen, (15, 20, 30), (0, 0, WIDTH, 50))
    pygame.draw.line(_screen, (255, 200, 50), (0, 50), (WIDTH, 50), 3)

    # Title (styled)
    t_surf = render_styled_text("Selecione a Dificuldade", font_big, (255, 255, 255),
                                outline_color=(10, 20, 50), outline_width=3,
                                gradient=((255, 255, 255), (180, 200, 255)))
    _screen.blit(t_surf, (WIDTH // 2 - t_surf.get_width() // 2, 8))

    levels = [
        ("Nivel 1", "1 Guindaste", "Velocidade baixa. Ideal para aprender.", (70, 180, 70)),
        ("Nivel 2", "2 Guindastes", "Velocidade media. Mais desafiador.", (70, 150, 255)),
        ("Nivel 3", "3 Guindastes", "Ritmo intenso. Para experts!", (255, 100, 100)),
    ]

    start_y = 100
    spacing = 115

    for i, (name, sub, desc, accent) in enumerate(levels):
        is_sel = (i + 1 == state.selected_level)
        rect = pygame.Rect(WIDTH // 2 - 170, start_y + i * spacing, 340, 95)

        # Shadow
        shadow_rect = rect.copy()
        shadow_rect.y += 6
        pygame.draw.rect(_screen, (10, 10, 15), shadow_rect, border_radius=12)

        # Selection glow
        if is_sel:
            for thickness in range(1, 6):
                alpha = 120 // thickness
                glow = pygame.Surface((rect.w + thickness * 2, rect.h + thickness * 2), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*accent, alpha), glow.get_rect(), border_radius=14, width=1)
                _screen.blit(glow, (rect.x - thickness, rect.y - thickness))

        # Card body
        fill_col = (55, 62, 80) if is_sel else (35, 40, 55)
        pygame.draw.rect(_screen, fill_col, rect, border_radius=12)
        pygame.draw.rect(_screen, accent if is_sel else (50, 55, 70), rect, 3 if is_sel else 1, border_radius=12)

        # Accent stripe on the left
        stripe = pygame.Rect(rect.x + 4, rect.y + 8, 4, rect.h - 16)
        pygame.draw.rect(_screen, accent, stripe, border_radius=2)

        # Name (styled)
        name_col = (255, 255, 255) if is_sel else (180, 190, 200)
        n_surf = render_styled_text(name, font_med, name_col, outline_color=(0, 0, 0), outline_width=2)
        _screen.blit(n_surf, (rect.x + 18, rect.y + 12))

        # Subtitle (crane count)
        sub_col = accent if is_sel else (120, 130, 150)
        s_txt = font_sm.render(sub, True, sub_col)
        _screen.blit(s_txt, (rect.x + 18, rect.y + 40))

        # Description
        d_txt = font_xs.render(desc, True, (160, 170, 190) if is_sel else (100, 110, 130))
        _screen.blit(d_txt, (rect.x + 18, rect.y + 64))

        # Crane count dots on the right
        dot_x = rect.right - 30
        dot_y = rect.y + rect.h // 2 - 12
        for d in range(i + 1):
            pygame.draw.circle(_screen, accent if is_sel else (80, 85, 100), (dot_x, dot_y + d * 14), 5)
            if is_sel:
                pygame.draw.circle(_screen, (255, 255, 255), (dot_x, dot_y + d * 14), 2)

    # Footer navigation bar
    footer_y = total_h - 45
    pygame.draw.rect(_screen, (15, 18, 25), (0, footer_y, WIDTH, 45))
    pygame.draw.line(_screen, (50, 55, 75), (0, footer_y), (WIDTH, footer_y), 2)

    keys = [("SETAS", "Selecionar"), ("ENTER", "Jogar"), ("ESC", "Voltar")]
    total_keys_w = 0
    key_renders = []
    for key, label in keys:
        k_surf = font_sm.render(key, True, (255, 220, 100))
        l_surf = font_sm.render(f" {label}  ", True, (150, 155, 170))
        key_renders.append((k_surf, l_surf))
        total_keys_w += k_surf.get_width() + l_surf.get_width()
    draw_kx = WIDTH // 2 - total_keys_w // 2
    for k_surf, l_surf in key_renders:
        _screen.blit(k_surf, (draw_kx, footer_y + 12))  # Adjust Y slightly up
        draw_kx += k_surf.get_width()
        _screen.blit(l_surf, (draw_kx, footer_y + 12))
        draw_kx += l_surf.get_width()

    draw_mobile_controls()


    pygame.display.flip()
