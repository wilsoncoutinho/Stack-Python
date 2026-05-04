import re

# Update renderer.py
with open('renderer.py', 'r', encoding='utf-8') as f:
    r_content = f.read()

mobile_func = '''
def draw_mobile_controls():
    if not _screen: return
    try:
        from constants import CONTROLS_H
    except ImportError:
        return
    ctrl_y = HEIGHT + HUD_H
    
    pygame.draw.rect(_screen, (190, 195, 180), (0, ctrl_y, WIDTH, CONTROLS_H))
    pygame.draw.line(_screen, (160, 165, 150), (0, ctrl_y), (WIDTH, ctrl_y), 4)
    pygame.draw.line(_screen, (220, 225, 210), (0, ctrl_y+4), (WIDTH, ctrl_y+4), 2)
    
    d_x, d_y = 80, ctrl_y + 90
    d_w, d_h = 45, 45
    d_color, d_glow = (40, 42, 45), (60, 65, 70)
    
    rects = [
        (d_x - d_w//2, d_y - d_h*1.5, d_w, d_h),
        (d_x - d_w//2, d_y + d_h*0.5, d_w, d_h),
        (d_x - d_w*1.5, d_y - d_h//2, d_w, d_h),
        (d_x + d_w*0.5, d_y - d_h//2, d_w, d_h),
        (d_x - d_w//2, d_y - d_h//2, d_w, d_h)
    ]
    for r in rects:
        pygame.draw.rect(_screen, d_color, r)
        pygame.draw.rect(_screen, d_glow, r, 2)
        
    btn_r = 25
    a_x, a_y = WIDTH - 60, ctrl_y + 80
    b_x, b_y = WIDTH - 130, ctrl_y + 110
    
    pygame.draw.circle(_screen, (150, 40, 60), (a_x, a_y), btn_r)
    pygame.draw.circle(_screen, (200, 60, 80), (a_x, a_y), btn_r, 3)
    a_txt = font_sm.render("A", True, (240, 200, 200))
    _screen.blit(a_txt, (a_x - a_txt.get_width()//2, a_y - a_txt.get_height()//2))
    
    pygame.draw.circle(_screen, (150, 40, 60), (b_x, b_y), btn_r)
    pygame.draw.circle(_screen, (200, 60, 80), (b_x, b_y), btn_r, 3)
    b_txt = font_sm.render("B", True, (240, 200, 200))
    _screen.blit(b_txt, (b_x - b_txt.get_width()//2, b_y - b_txt.get_height()//2))
    
    st_w, st_h = 35, 12
    st_x, st_y = WIDTH // 2 + 20, ctrl_y + 160
    se_x, se_y = WIDTH // 2 - 40, ctrl_y + 160
    
    pygame.draw.rect(_screen, (60, 60, 60), (st_x - st_w//2, st_y - st_h//2, st_w, st_h), border_radius=6)
    pygame.draw.rect(_screen, (60, 60, 60), (se_x - st_w//2, se_y - st_h//2, st_w, st_h), border_radius=6)
'''

if 'def draw_mobile_controls' not in r_content:
    # Insert function before draw_title
    r_content = r_content.replace('def draw_title', mobile_func + '\\n\\ndef draw_title')
    
    # Inject it before flip calls
    r_content = re.sub(r'(\s+)pygame\.display\.flip\(\)', r'\1draw_mobile_controls()\n\1pygame.display.flip()', r_content)
    
    with open('renderer.py', 'w', encoding='utf-8') as f:
        f.write(r_content)


# Update game.py
with open('game.py', 'r', encoding='utf-8') as f:
    g_content = f.read()

game_inject = '''
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
    d_x, d_y, d_w, d_h = 80, ctrl_y + 90, 45, 45
    if math.hypot(x - d_x, y - d_y) < 90:
        if x < d_x - 15: return pygame.K_LEFT
        if x > d_x + 15: return pygame.K_RIGHT
        if y < d_y - 15: return pygame.K_UP
        if y > d_y + 15: return pygame.K_DOWN
        return None
    if math.hypot(x - (WIDTH - 60), y - (ctrl_y + 80)) < 35: return pygame.K_SPACE
    if math.hypot(x - (WIDTH - 130), y - (ctrl_y + 110)) < 35: return pygame.K_ESCAPE
    if abs(x - (WIDTH // 2 + 20)) < 30 and abs(y - (ctrl_y + 160)) < 20: return pygame.K_RETURN
    if abs(x - (WIDTH // 2 - 40)) < 30 and abs(y - (ctrl_y + 160)) < 20: return pygame.K_ESCAPE
    return None

'''

if 'simulated_keys' not in g_content:
    g_content = g_content.replace('def reset_game', game_inject + '\\ndef reset_game')
    
    # Inject event interceptor into run_game loop
    interceptor = '''
        for event in pygame.event.get():
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                k = get_touch_key(*event.pos)
                if k:
                    is_down = (event.type == pygame.MOUSEBUTTONDOWN)
                    simulated_keys[k] = is_down
                    if is_down: pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k))
            pygame.event.post(event)
        events = pygame.event.get()
'''
    g_content = re.sub(r'(\s+)while True:', r'\1while True:\n' + interceptor, g_content)
    g_content = g_content.replace('for event in pygame.event.get():', 'for event in events:')
    
    # Update teclas
    g_content = g_content.replace(
        'teclas = {"esquerda": keys[pygame.K_LEFT] or keys[pygame.K_a], "direita": keys[pygame.K_RIGHT] or keys[pygame.K_d]}',
        'teclas = {"esquerda": keys[pygame.K_LEFT] or keys[pygame.K_a] or simulated_keys.get(pygame.K_LEFT, False), "direita": keys[pygame.K_RIGHT] or keys[pygame.K_d] or simulated_keys.get(pygame.K_RIGHT, False)}'
    )
    
    with open('game.py', 'w', encoding='utf-8') as f:
        f.write(g_content)

print("Restoration complete")
