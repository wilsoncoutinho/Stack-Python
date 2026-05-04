"""
Stack Attack Reborn — Audio System

Music playback, dynamic tempo system, and sound effect helpers.
"""
import os
import pygame
from constants import (
    ASSETS, GAMEPLAY_MUSIC_FILES, MUSIC_THRESHOLDS,
)
import state

import io

# ---------------------------------------------------------------------------
# Mixer state
# ---------------------------------------------------------------------------
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
    SOUND_OK = True
except Exception:
    SOUND_OK = False

# Music memory cache to prevent disk-load stutter
_music_data = {}

def pre_load_music_assets():
    """Load all MIDI files into memory at startup."""
    if not SOUND_OK:
        return
    tracks = GAMEPLAY_MUSIC_FILES + ["title.mid", "gameover.mid"]
    for name in tracks:
        path = os.path.join(ASSETS, name)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    _music_data[name] = f.read()
            except Exception:
                pass

# Run pre-load immediately
pre_load_music_assets()

current_music_level = 0
gameplay_music_playing = False


# ---------------------------------------------------------------------------
# Music helpers
# ---------------------------------------------------------------------------
def play_music(name, loops=0):
    if not SOUND_OK:
        return
    
    try:
        if name in _music_data:
            # Load from memory buffer (BytesIO) to avoid I/O blocking
            mem_file = io.BytesIO(_music_data[name])
            pygame.mixer.music.load(mem_file)
            pygame.mixer.music.play(loops)
        else:
            # Fallback to disk
            path = os.path.join(ASSETS, name)
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(loops)
    except Exception:
        pass


def stop_music():
    if SOUND_OK:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass


def pause_music():
    if SOUND_OK:
        try:
            pygame.mixer.music.pause()
        except Exception:
            pass


def unpause_music():
    if SOUND_OK:
        try:
            pygame.mixer.music.unpause()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Dynamic gameplay music
# ---------------------------------------------------------------------------
def get_music_level_for_difficulty(diff):
    """Returns the music level (0-4) for a given difficulty value."""
    level = 0
    for i, threshold in enumerate(MUSIC_THRESHOLDS):
        if diff >= threshold:
            level = i
    return level


def start_gameplay_music():
    """Start gameplay music at the appropriate tempo for current difficulty."""
    global current_music_level, gameplay_music_playing
    current_music_level = get_music_level_for_difficulty(state.difficulty)
    play_music(GAMEPLAY_MUSIC_FILES[current_music_level], loops=-1)
    gameplay_music_playing = True


def update_gameplay_music():
    """Check if difficulty warrants a tempo change and switch tracks."""
    global current_music_level, gameplay_music_playing
    if not gameplay_music_playing:
        return
    new_level = get_music_level_for_difficulty(state.difficulty)
    if new_level != current_music_level:
        current_music_level = new_level
        # Use a short fadeout to make the transition more fluid and avoid pops/stutter
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(500)
            # We can't easily wait for fadeout completion without blocking, 
            # so we just load and play which will interrupt the fade anyway but smoother
        play_music(GAMEPLAY_MUSIC_FILES[current_music_level], loops=-1)


def stop_gameplay_music():
    """Stop gameplay music tracking."""
    global gameplay_music_playing
    gameplay_music_playing = False
    stop_music()


# ---------------------------------------------------------------------------
# Sound effects
# ---------------------------------------------------------------------------
def load_sound(filename):
    """Load a sound effect and return the Sound object."""
    if not SOUND_OK:
        return None
    path = os.path.join(ASSETS, filename)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            pass
    return None


def play_sound(sound):
    """Play a sound effect if it's loaded."""
    if sound and SOUND_OK:
        try:
            sound.play()
        except Exception:
            pass


# Pre-loaded sound effects
sound_jump = load_sound("sounds/jump.ogg")
sound_super_jump = load_sound("sounds/super_jump.ogg")
sound_push = load_sound("sounds/push.ogg")
sound_land = load_sound("sounds/land.ogg")
sound_explode = load_sound("sounds/explode.ogg")
sound_powerup = load_sound("sounds/powerup.ogg")
sound_bomb = load_sound("sounds/bomb.ogg")
sound_stun = load_sound("sounds/stun.ogg")
sound_combo = load_sound("sounds/combo.ogg")
sound_line_clear = load_sound("sounds/line_clear.ogg")
sound_game_over_sfx = load_sound("sounds/game_over.ogg")
sound_menu_move = load_sound("sounds/menu_move.ogg")
sound_menu_select = load_sound("sounds/menu_select.ogg")
sound_helmet = load_sound("sounds/helmet.ogg")
