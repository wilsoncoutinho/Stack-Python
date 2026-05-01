"""Extended font check - console only, no window."""
import pygame
import os

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONT_PATH = os.path.join(ASSETS, "jetpack-joyride-revived.ttf", "jetpack-joyride-revived.ttf")

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
screen = pygame.display.set_mode((1, 1))

font = pygame.font.Font(FONT_PATH, 24)

# Full printable ASCII
ascii_chars = [chr(c) for c in range(33, 127)]
# Portuguese accented chars
pt_chars = list("ÁáÀàÂâÃãÉéÊêÍíÓóÔôÕõÚúÜüÇç")
# All chars to test
test_chars = ascii_chars + pt_chars

missing = []
present = []
for ch in test_chars:
    metrics = font.metrics(ch)
    if not metrics or not metrics[0]:
        missing.append(ch)
    else:
        minx, maxx, miny, maxy, advance = metrics[0]
        if advance <= 0 or (maxx - minx) <= 0:
            missing.append(ch)
        else:
            present.append(ch)

print(f"Font: {os.path.basename(FONT_PATH)}")
print(f"Present glyphs: {len(present)}")
print(f"Missing glyphs: {len(missing)}")
print()

if missing:
    print("MISSING CHARACTERS:")
    for ch in missing:
        print(f"  U+{ord(ch):04X} = '{ch}'")

# Now check which missing chars are actually USED in the game
game_strings = [
    "PONTOS", "SUPER", "NIVEL", "BOMBAS", "CAPACETE", "COMBO",
    "GAME OVER", "PONTOS TOTAIS", "NOVO RECORDE", "R REINICIAR", "Q SAIR",
    "PAUSE", "CRATE COLA", "Beba e pule alto!", "Voltando em", "Aguarde",
    "PRESSIONE ENTER PARA PULAR", "Pressione ENTER para jogar",
    "SELECIONE O PERSONAGEM", "EQUIPADO", "SETAS", "Navegar", "Jogar", "Sair",
    "PART TIME PETE", "LAZY LIZZIE", "FORKLIFT FRANK", "WAREHOUSE WILL",
    "CRATE CRAZY CATH", "SUPER STACKER SAM",
    "Basico. Sem super pulos.", "Rapida. 4 super pulos.",
    "Rapido, 1 super pulo.", "Agil. 2 super pulos.",
    "Muito rapida. 3 super pulos.", "O melhor! 5 super pulos + 3 bombas.",
    "Selecione a Dificuldade", "Nivel", "Guindaste", "Guindastes",
    "Selecionar", "Voltar",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "X", "!", ".", ",", "+", ":",
    # Dynamic score display could show any number
]

used_chars = set()
for s in game_strings:
    used_chars.update(s)
used_chars.discard(' ')

missing_used = [ch for ch in missing if ch in used_chars]
print()
print(f"Missing chars ACTUALLY USED in game: {len(missing_used)}")
if missing_used:
    for ch in missing_used:
        print(f"  U+{ord(ch):04X} = '{ch}' - PROBLEM!")
else:
    print("  None - all game text renders correctly!")

# Also check digits 6, 7, 8 specifically (for scores)
print()
print("DIGIT CHECK:")
for d in "0123456789":
    m = font.metrics(d)
    status = "OK" if m and m[0] and m[0][4] > 0 else "MISSING!"
    print(f"  '{d}': {status}")

# Check colon specifically (was removed from some strings)
print()
print("SPECIAL CHAR CHECK:")
for ch in ":;-_()[]{}|\\/<>@#$%^&*~`\"'":
    m = font.metrics(ch)
    ok = m and m[0] and m[0][4] > 0 and (m[0][1] - m[0][0]) > 0
    print(f"  '{ch}' (U+{ord(ch):04X}): {'OK' if ok else 'MISSING'}")

pygame.quit()
