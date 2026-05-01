"""Deep visual test - render each problematic char at each size and save."""
import pygame
import os

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONT_PATH = os.path.join(ASSETS, "jetpack-joyride-revived.ttf", "jetpack-joyride-revived.ttf")

pygame.init()
screen = pygame.display.set_mode((600, 800))
screen.fill((30, 30, 50))

sizes = [8, 10, 16, 20, 24, 32]
test_chars = "!+,.:;-_()[]{}|@#$%^&*~`\"'<>/\\?0123456789"

y = 10
for size in sizes:
    font = pygame.font.Font(FONT_PATH, size)
    label = font.render(f"Size {size}px: ", True, (255, 210, 50))
    screen.blit(label, (10, y))
    
    x = 10
    y += label.get_height() + 2
    for ch in test_chars:
        ch_surf = font.render(ch, True, (255, 255, 255))
        # Draw a small background box for visibility
        pygame.draw.rect(screen, (60, 60, 80), (x, y, ch_surf.get_width() + 4, ch_surf.get_height() + 2))
        screen.blit(ch_surf, (x + 2, y + 1))
        x += ch_surf.get_width() + 6
        if x > 560:
            x = 10
            y += ch_surf.get_height() + 4
    y += 30

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font_screenshots")
os.makedirs(OUT_DIR, exist_ok=True)
pygame.image.save(screen, os.path.join(OUT_DIR, "07_char_sizes.png"))
print("Saved 07_char_sizes.png")
pygame.quit()
