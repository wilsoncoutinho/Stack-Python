"""Check which characters the custom font supports vs what the game renders."""
import pygame
import os
import sys

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONT_PATH = os.path.join(ASSETS, "jetpack-joyride-revived.ttf", "jetpack-joyride-revived.ttf")

pygame.init()
screen = pygame.display.set_mode((100, 100))

# All text strings used in the game (extracted from main.py)
game_texts = [
    # HUD
    "PONTOS 12345",
    "SUPER 5",
    "NIVEL 3",
    "BOMBAS 3",
    "CAPACETE 5",
    "COMBO X3!",
    # Game Over
    "GAME OVER",
    "PONTOS TOTAIS",
    "NOVO RECORDE",
    "RECORDE 999",
    "R REINICIAR   Q SAIR",
    # Pause / Ad
    "PAUSE",
    "CRATE COLA",
    "Beba e pule alto!",
    "Voltando em 5...",
    "Aguarde 3s...",
    "PRESSIONE ENTER PARA PULAR",
    # Title
    "Pressione ENTER para jogar",
    # Char Select
    "SELECIONE O PERSONAGEM",
    "EQUIPADO",
    "BOMBAS",
    "SETAS", "Navegar", "ENTER", "Jogar", "ESC", "Sair",
    # Character names
    "PART TIME PETE",
    "LAZY LIZZIE",
    "FORKLIFT FRANK",
    "WAREHOUSE WILL",
    "CRATE CRAZY CATH",
    "SUPER STACKER SAM",
    # Character descriptions
    "Basico. Sem super pulos.",
    "Rapida. 4 super pulos.",
    "Rapido, 1 super pulo.",
    "Agil. 2 super pulos.",
    "Muito rapida. 3 super pulos.",
    "O melhor! 5 super pulos + 3 bombas.",
    "RECORDE 0",
    # Level Select
    "Selecione a Dificuldade",
    "Nivel 1", "1 Guindaste",
    "Nivel 2", "2 Guindastes",
    "Nivel 3", "3 Guindastes",
    "Selecionar", "Voltar",
]

# Collect all unique characters used
all_chars = set()
for text in game_texts:
    all_chars.update(text)

# Sort for readability
all_chars = sorted(all_chars)

print(f"Font file: {FONT_PATH}")
print(f"Font exists: {os.path.exists(FONT_PATH)}")
print(f"\nTotal unique characters needed: {len(all_chars)}")
print(f"Characters: {''.join(all_chars)}")

# Load font and check glyph metrics
font = pygame.font.Font(FONT_PATH, 24)
print(f"\nFont loaded successfully: {font}")

missing = []
present = []

for ch in all_chars:
    metrics = font.metrics(ch)
    if metrics and metrics[0]:
        # metrics returns [(minx, maxx, miny, maxy, advance)]
        # If advance is 0 or the glyph doesn't exist, it would be missing
        minx, maxx, miny, maxy, advance = metrics[0]
        if advance > 0 and (maxx - minx) > 0:
            present.append(ch)
        else:
            missing.append(ch)
    else:
        missing.append(ch)

print(f"\n--- PRESENT GLYPHS ({len(present)}) ---")
for ch in present:
    m = font.metrics(ch)[0]
    print(f"  '{ch}' (U+{ord(ch):04X}) - advance={m[4]}, width={m[1]-m[0]}")

print(f"\n--- MISSING GLYPHS ({len(missing)}) ---")
for ch in missing:
    print(f"  '{ch}' (U+{ord(ch):04X}) - {'SPACE' if ch == ' ' else repr(ch)}")

# Visual test: render each string and check for "tofu" (blank rectangles)
print("\n\n--- VISUAL RENDER TEST ---")
for text in game_texts:
    surf = font.render(text, True, (255, 255, 255))
    # Check if any individual character has zero-width rendering
    broken = []
    for ch in text:
        if ch == ' ':
            continue
        ch_surf = font.render(ch, True, (255, 255, 255))
        metrics = font.metrics(ch)
        if not metrics or not metrics[0] or metrics[0][4] <= 0:
            broken.append(ch)
    if broken:
        print(f"  BROKEN: '{text}' -> missing: {broken}")
    else:
        print(f"  OK: '{text}'")

pygame.quit()
