"""Capture screenshots of every game screen to visually inspect fonts."""
import pygame
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONT_PATH = os.path.join(ASSETS, "jetpack-joyride-revived.ttf", "jetpack-joyride-revived.ttf")

pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except:
    pass

TILE_SIZE = 40
COLS, ROWS = 12, 12
WIDTH = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE
HUD_H = 48
screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD_H))

font_big = pygame.font.Font(FONT_PATH, 20)
font_med = pygame.font.Font(FONT_PATH, 16)
font_sm = pygame.font.Font(FONT_PATH, 10)
font_xs = pygame.font.Font(FONT_PATH, 8)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font_screenshots")
os.makedirs(OUT_DIR, exist_ok=True)

# ---- Screen 1: All HUD text ----
screen.fill((30, 30, 50))
y = 10
texts = [
    (font_big, "GAME OVER", (255, 255, 255)),
    (font_med, "PONTOS 12345", (255, 210, 50)),
    (font_med, "SUPER 5", (100, 255, 100)),
    (font_sm, "NIVEL 3", (180, 200, 220)),
    (font_sm, "BOMBAS 3", (255, 120, 120)),
    (font_sm, "CAPACETE 5", (100, 255, 100)),
    (font_sm, "COMBO X3!", (255, 150, 50)),
    (font_xs, "PONTOS TOTAIS", (140, 150, 170)),
    (font_sm, "NOVO RECORDE", (100, 255, 100)),
    (font_sm, "RECORDE 999", (255, 210, 50)),
    (font_sm, "R REINICIAR   Q SAIR", (200, 210, 230)),
]
for fnt, txt, col in texts:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 8
pygame.image.save(screen, os.path.join(OUT_DIR, "01_hud_texts.png"))
print("Saved 01_hud_texts.png")

# ---- Screen 2: Pause/Ad text ----
screen.fill((30, 30, 50))
y = 10
texts = [
    (font_big, "PAUSE", (0, 255, 0)),
    (font_med, "CRATE COLA", (200, 30, 30)),
    (font_xs, "Beba e pule alto!", (40, 40, 40)),
    (font_xs, "Voltando em 5...", (80, 80, 80)),
    (font_sm, "Aguarde 3s...", (150, 150, 150)),
    (font_sm, "PRESSIONE ENTER PARA PULAR", (0, 255, 0)),
]
for fnt, txt, col in texts:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 8
pygame.image.save(screen, os.path.join(OUT_DIR, "02_pause_ad_texts.png"))
print("Saved 02_pause_ad_texts.png")

# ---- Screen 3: Title / Char Select ----
screen.fill((30, 30, 50))
y = 10
texts = [
    (font_med, "Pressione ENTER para jogar", (200, 200, 255)),
    (font_big, "SELECIONE O PERSONAGEM", (255, 255, 255)),
    (font_xs, "EQUIPADO", (20, 20, 25)),
    (font_sm, "SETAS", (255, 210, 50)),
    (font_sm, "Navegar", (210, 215, 230)),
    (font_sm, "ENTER", (255, 210, 50)),
    (font_sm, "Jogar", (210, 215, 230)),
    (font_sm, "ESC", (255, 210, 50)),
    (font_sm, "Sair", (210, 215, 230)),
]
for fnt, txt, col in texts:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 8
pygame.image.save(screen, os.path.join(OUT_DIR, "03_title_charsel_texts.png"))
print("Saved 03_title_charsel_texts.png")

# ---- Screen 4: Character Names & Descriptions ----
screen.fill((30, 30, 50))
y = 10
char_texts = [
    (font_sm, "PART TIME PETE", (255, 255, 255)),
    (font_xs, "Basico. Sem super pulos.", (180, 190, 200)),
    (font_sm, "LAZY LIZZIE", (255, 255, 255)),
    (font_xs, "Rapida. 4 super pulos.", (180, 190, 200)),
    (font_sm, "FORKLIFT FRANK", (255, 255, 255)),
    (font_xs, "Rapido, 1 super pulo.", (180, 190, 200)),
    (font_sm, "WAREHOUSE WILL", (255, 255, 255)),
    (font_xs, "Agil. 2 super pulos.", (180, 190, 200)),
    (font_sm, "CRATE CRAZY CATH", (255, 255, 255)),
    (font_xs, "Muito rapida. 3 super pulos.", (180, 190, 200)),
    (font_sm, "SUPER STACKER SAM", (255, 255, 255)),
    (font_xs, "O melhor! 5 super pulos + 3 bombas.", (180, 190, 200)),
    (font_xs, "RECORDE 0", (120, 130, 145)),
    (font_xs, "BOMBAS", (255, 255, 255)),
]
for fnt, txt, col in char_texts:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 6
pygame.image.save(screen, os.path.join(OUT_DIR, "04_char_names_descs.png"))
print("Saved 04_char_names_descs.png")

# ---- Screen 5: Level Select ----
screen.fill((30, 30, 50))
y = 10
texts = [
    (font_big, "Selecione a Dificuldade", (255, 255, 255)),
    (font_med, "Nivel 1", (255, 255, 255)),
    (font_sm, "1 Guindaste", (150, 200, 255)),
    (font_med, "Nivel 2", (255, 255, 255)),
    (font_sm, "2 Guindastes", (150, 200, 255)),
    (font_med, "Nivel 3", (255, 255, 255)),
    (font_sm, "3 Guindastes", (150, 200, 255)),
    (font_xs, "SETAS", (255, 220, 100)),
    (font_xs, "Selecionar", (150, 155, 170)),
    (font_xs, "ENTER", (255, 220, 100)),
    (font_xs, "Jogar", (150, 155, 170)),
    (font_xs, "ESC", (255, 220, 100)),
    (font_xs, "Voltar", (150, 155, 170)),
]
for fnt, txt, col in texts:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 8
pygame.image.save(screen, os.path.join(OUT_DIR, "05_level_select_texts.png"))
print("Saved 05_level_select_texts.png")

# ---- Screen 6: Dynamic score values ----
screen.fill((30, 30, 50))
y = 10
for i in range(0, 10000, 1111):
    s = font_med.render(f"PONTOS {i}", True, (255, 210, 50))
    screen.blit(s, (20, y))
    y += s.get_height() + 4
for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
    s = font_med.render(f"SUPER {i}", True, (100, 255, 100))
    screen.blit(s, (250, 10 + i * 28))
pygame.image.save(screen, os.path.join(OUT_DIR, "06_dynamic_scores.png"))
print("Saved 06_dynamic_scores.png")

print(f"\nAll screenshots saved to: {OUT_DIR}")
pygame.quit()
