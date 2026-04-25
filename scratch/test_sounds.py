"""Quick test to verify all sound effects load properly."""
import pygame
import os

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

sound_files = [
    "sounds/jump.wav",
    "sounds/super_jump.wav",
    "sounds/push.wav",
    "sounds/land.wav",
    "sounds/explode.wav",
    "sounds/powerup.wav",
    "sounds/bomb.wav",
    "sounds/stun.wav",
    "sounds/combo.wav",
    "sounds/line_clear.wav",
    "sounds/game_over.wav",
    "sounds/menu_move.wav",
    "sounds/menu_select.wav",
    "sounds/helmet.wav",
]

all_ok = True
for sf in sound_files:
    path = os.path.join(ASSETS, sf)
    exists = os.path.exists(path)
    if exists:
        try:
            s = pygame.mixer.Sound(path)
            print(f"  OK {sf} (length: {s.get_length():.3f}s)")
        except Exception as e:
            print(f"  FAIL {sf}: {e}")
            all_ok = False
    else:
        print(f"  MISSING {sf}")
        all_ok = False

# Test MIDI music files
midi_files = ["title.mid", "fullrow.mid", "gameover.mid", "extra.mid"]
for mf in midi_files:
    path = os.path.join(ASSETS, mf)
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            print(f"  OK {mf} (MIDI)")
        except Exception as e:
            print(f"  FAIL {mf}: {e}")
            all_ok = False
    else:
        print(f"  MISSING {mf}")
        all_ok = False

print(f"\n{'All sounds loaded successfully!' if all_ok else 'Some sounds failed to load.'}")
pygame.quit()
