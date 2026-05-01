"""Extended font test: check ALL possible characters including accented ones,
numbers 6-8 which can appear dynamically, and any edge cases."""
import pygame
import os

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONT_PATH = os.path.join(ASSETS, "jetpack-joyride-revived.ttf", "jetpack-joyride-revived.ttf")

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Font Glyph Test")

font = pygame.font.Font(FONT_PATH, 24)
font_sm = pygame.font.Font(FONT_PATH, 16)

# Check ALL printable ASCII + common Portuguese chars
test_ranges = [
    ("Basic ASCII", "".join(chr(c) for c in range(32, 127))),
    ("Numbers 0-9", "0123456789"),
    ("Portuguese accents", "ÁáÀàÂâÃãÉéÊêÍíÓóÔôÕõÚúÜüÇç"),
    ("Common symbols", "!@#$%^&*()_+-=[]{}|;':\",./<>?~`"),
    ("Dynamic game text", "PONTOS 67890 SUPER NIVEL COMBO X99!"),
    ("HUD with colon", "PONTOS: 123  NIVEL: 5  COMBO: X3"),
]

screen.fill((30, 30, 40))
y = 20

# Check each character individually
all_missing = []
for label, chars in test_ranges:
    missing_in_set = []
    for ch in chars:
        if ch == ' ':
            continue
        metrics = font.metrics(ch)
        if not metrics or not metrics[0] or metrics[0][4] <= 0 or (metrics[0][1] - metrics[0][0]) <= 0:
            missing_in_set.append(ch)
            all_missing.append((ch, ord(ch)))
    
    # Render the test string
    surf = font_sm.render(f"{label}:", True, (255, 210, 50))
    screen.blit(surf, (20, y))
    y += 25
    
    # Render each char, highlight missing ones
    x = 20
    for ch in chars:
        if ch == ' ':
            x += 10
            continue
        is_missing = ch in missing_in_set
        color = (255, 60, 60) if is_missing else (200, 200, 200)
        ch_surf = font_sm.render(ch, True, color)
        if is_missing:
            pygame.draw.rect(screen, (100, 30, 30), (x-1, y-1, ch_surf.get_width()+2, ch_surf.get_height()+2))
        screen.blit(ch_surf, (x, y))
        x += ch_surf.get_width() + 2
        if x > 760:
            x = 20
            y += 22
    y += 30

# Summary
y += 10
summary_text = f"MISSING GLYPHS: {len(all_missing)}"
s = font.render(summary_text, True, (255, 100, 100) if all_missing else (100, 255, 100))
screen.blit(s, (20, y))
y += 35

if all_missing:
    for ch, code in all_missing:
        txt = f"  U+{code:04X} = '{ch}'"
        s = font_sm.render(txt, True, (255, 150, 150))
        screen.blit(s, (20, y))
        y += 22

# Print to console too
print(f"\n{'='*60}")
print(f"FONT GLYPH ANALYSIS RESULTS")
print(f"{'='*60}")
print(f"Font: {FONT_PATH}")
print(f"Total missing glyphs: {len(all_missing)}")
if all_missing:
    print(f"\nMissing characters:")
    for ch, code in all_missing:
        print(f"  U+{code:04X} = '{ch}' ({repr(ch)})")
else:
    print("All needed glyphs are present!")

pygame.display.flip()

# Wait for user to close
running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
            running = False
    pygame.time.wait(50)

pygame.quit()
