"""Capture screenshots using the HybridFont system to verify the fix."""
import pygame
import os, math

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

pygame.init()
TILE_SIZE = 40
COLS, ROWS = 12, 12
WIDTH = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE
HUD_H = 48
screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD_H))

# ---- Replicate the HybridFont from main.py ----
_CUSTOM_FONT_CHARS = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.$"
)

def _get_fallback_font(size):
    for name in ["Impact", "Arial Black", "Segoe UI", "Verdana"]:
        try:
            f = pygame.font.SysFont(name, size, bold=True)
            if f:
                return f
        except:
            continue
    return pygame.font.SysFont(None, size)

class HybridFont:
    def __init__(self, custom_font, fallback_font, size):
        self.custom = custom_font
        self.fallback = fallback_font
        self._size = size

    def _font_for_char(self, ch):
        if ch in _CUSTOM_FONT_CHARS or ch == ' ':
            return self.custom
        return self.fallback

    def render(self, text, antialias, color, background=None):
        if all(c in _CUSTOM_FONT_CHARS or c == ' ' for c in text):
            if background:
                return self.custom.render(text, antialias, color, background)
            return self.custom.render(text, antialias, color)

        char_surfs = []
        total_w = 0
        max_h = 0
        for ch in text:
            font = self._font_for_char(ch)
            s = font.render(ch, antialias, color) if not background else font.render(ch, antialias, color, background)
            char_surfs.append(s)
            total_w += s.get_width()
            max_h = max(max_h, s.get_height())

        if background:
            result = pygame.Surface((total_w, max_h))
            result.fill(background)
        else:
            result = pygame.Surface((total_w, max_h), pygame.SRCALPHA)

        x = 0
        for s in char_surfs:
            y_off = max_h - s.get_height()
            result.blit(s, (x, y_off))
            x += s.get_width()
        return result

    def size(self, text):
        if all(c in _CUSTOM_FONT_CHARS or c == ' ' for c in text):
            return self.custom.size(text)
        w = h = 0
        for ch in text:
            font = self._font_for_char(ch)
            cw, ch2 = font.size(ch)
            w += cw
            h = max(h, ch2)
        return (w, h)

FONT_PATH = os.path.join(ASSETS, "jetpack-joyride-revived.ttf", "jetpack-joyride-revived.ttf")

def get_font(size):
    custom = pygame.font.Font(FONT_PATH, size)
    fallback = _get_fallback_font(size)
    return HybridFont(custom, fallback, size)

font_big = get_font(20)
font_med = get_font(16)
font_sm = get_font(10)
font_xs = get_font(8)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font_screenshots_fixed")
os.makedirs(OUT_DIR, exist_ok=True)

# ---- Screen 1: HUD text ----
screen.fill((30, 30, 50))
y = 10
for fnt, txt, col in [
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
]:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 8
pygame.image.save(screen, os.path.join(OUT_DIR, "01_hud.png"))
print("Saved 01_hud.png")

# ---- Screen 2: Pause/Ad text ----
screen.fill((30, 30, 50))
y = 10
for fnt, txt, col in [
    (font_big, "PAUSE", (0, 255, 0)),
    (font_med, "CRATE COLA", (200, 30, 30)),
    (font_xs, "Beba e pule alto!", (200, 200, 200)),
    (font_xs, "Voltando em 5...", (200, 200, 200)),
    (font_sm, "Aguarde 3s...", (150, 150, 150)),
    (font_sm, "PRESSIONE ENTER PARA PULAR", (0, 255, 0)),
]:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 8
pygame.image.save(screen, os.path.join(OUT_DIR, "02_pause_ad.png"))
print("Saved 02_pause_ad.png")

# ---- Screen 3: Character Names & Descriptions ----
screen.fill((30, 30, 50))
y = 10
for fnt, txt, col in [
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
]:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 6
pygame.image.save(screen, os.path.join(OUT_DIR, "03_char_descs.png"))
print("Saved 03_char_descs.png")

# ---- Screen 4: Level Select ----
screen.fill((30, 30, 50))
y = 10
for fnt, txt, col in [
    (font_big, "Selecione a Dificuldade", (255, 255, 255)),
    (font_med, "Nivel 1", (255, 255, 255)),
    (font_sm, "1 Guindaste", (150, 200, 255)),
    (font_med, "Nivel 2", (255, 255, 255)),
    (font_sm, "2 Guindastes", (150, 200, 255)),
    (font_med, "Nivel 3", (255, 255, 255)),
    (font_sm, "3 Guindastes", (150, 200, 255)),
]:
    s = fnt.render(txt, True, col)
    screen.blit(s, (20, y))
    y += s.get_height() + 8
pygame.image.save(screen, os.path.join(OUT_DIR, "04_level_select.png"))
print("Saved 04_level_select.png")

# ---- Screen 5: Special chars comparison (Before vs After) ----
screen.fill((30, 30, 50))
y = 10
# Show the problematic strings
problem_strings = [
    "COMBO X3!",
    "Rapido, 1 super pulo.",
    "O melhor! 5 super pulos + 3 bombas.",
    "Beba e pule alto!",
    "Voltando em 5...",
    "Aguarde 3s...",
]
label = font_sm.render("HYBRID FONT OUTPUT", True, (255, 210, 50))
screen.blit(label, (20, y))
y += label.get_height() + 8
for txt in problem_strings:
    s = font_xs.render(txt, True, (200, 200, 200))
    screen.blit(s, (20, y))
    y += s.get_height() + 6

# Compare with raw custom font (showing tofu)
y += 20
raw_font = pygame.font.Font(FONT_PATH, 8)
label2 = font_sm.render("RAW CUSTOM FONT", True, (255, 100, 100))
screen.blit(label2, (20, y))
y += label2.get_height() + 8
for txt in problem_strings:
    s = raw_font.render(txt, True, (200, 200, 200))
    screen.blit(s, (20, y))
    y += s.get_height() + 6

pygame.image.save(screen, os.path.join(OUT_DIR, "05_comparison.png"))
print("Saved 05_comparison.png")

print(f"\nAll saved to: {OUT_DIR}")
pygame.quit()
