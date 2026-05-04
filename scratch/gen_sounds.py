"""
Generate retro-style WAV sound effects for Stack Attack using procedural synthesis.
These replicate the feel of the original Siemens mobile game sounds.
"""
import os
import struct
import math
import random

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
OUTPUT = os.path.join(ASSETS, "sounds")
os.makedirs(OUTPUT, exist_ok=True)

SAMPLE_RATE = 22050


import soundfile as sf

def write_ogg(filename, samples, sample_rate=SAMPLE_RATE):
    """Write samples to an OGG file using soundfile."""
    path = os.path.join(OUTPUT, filename)
    try:
        sf.write(path, samples, sample_rate, format='OGG', subtype='VORBIS')
        print(f"  Created {filename} ({len(samples)} samples, {len(samples)/sample_rate:.2f}s)")
    except Exception as e:
        print(f"  Error writing {filename}: {e}")


def square_wave(freq, t):
    """Generate a square wave sample."""
    return 1.0 if (t * freq * 2) % 2 < 1 else -1.0


def triangle_wave(freq, t):
    """Generate a triangle wave sample."""
    phase = (t * freq) % 1.0
    return 4.0 * abs(phase - 0.5) - 1.0


def noise():
    """Generate white noise sample."""
    return random.uniform(-1.0, 1.0)


def sine_wave(freq, t):
    """Generate a sine wave sample."""
    return math.sin(2 * math.pi * freq * t)


def gen_jump():
    """Soft ascending chirp — gentle sine sweep with smooth fade."""
    duration = 0.12
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 350 + 450 * (progress ** 0.7)  # smooth curve up
        # Smooth envelope: fade in briefly, then fade out
        env = math.sin(progress * math.pi)  # bell-shaped
        amp = 0.35 * env
        s = (sine_wave(freq, t) * 0.7 +
             triangle_wave(freq * 1.5, t) * 0.2 +
             sine_wave(freq * 2, t) * 0.1) * amp
        samples.append(s)
    return samples


def gen_super_jump():
    """Higher-pitched soft ascending sweep with shimmer."""
    duration = 0.18
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 500 + 700 * (progress ** 0.6)  # smooth sweep up
        env = math.sin(progress * math.pi) * (1.0 - progress * 0.3)
        amp = 0.4 * env
        s = (sine_wave(freq, t) * 0.5 +
             triangle_wave(freq * 1.5, t) * 0.3 +
             sine_wave(freq * 3, t) * 0.08) * amp
        samples.append(s)
    return samples


def gen_push():
    """Short thud/scrape - box being pushed."""
    duration = 0.12
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 120 - 40 * progress
        amp = 0.5 * (1.0 - progress)
        s = (square_wave(freq, t) * 0.4 + noise() * 0.3) * amp
        samples.append(s)
    return samples


def gen_land():
    """Low thump when a crate lands."""
    duration = 0.1
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 80 - 30 * progress
        amp = 0.7 * max(0, 1.0 - progress * 1.5)
        s = sine_wave(freq, t) * amp + noise() * 0.1 * max(0, 1.0 - progress * 3)
        samples.append(s)
    return samples


def gen_explode():
    """Explosion/bang - noise burst with descending tone."""
    duration = 0.35
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 200 * (1.0 - progress * 0.8)
        amp = 0.8 * max(0, 1.0 - progress * 1.2)
        s = (noise() * 0.6 + 
             square_wave(freq, t) * 0.3 +
             sine_wave(freq * 0.5, t) * 0.2) * amp
        samples.append(s)
    return samples


def gen_powerup():
    """Ascending arpeggio - picking up a powerup."""
    duration = 0.3
    samples = []
    n = int(SAMPLE_RATE * duration)
    notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
    note_dur = duration / len(notes)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        note_idx = min(int(t / note_dur), len(notes) - 1)
        freq = notes[note_idx]
        amp = 0.5 * (1.0 - progress * 0.3)
        s = (triangle_wave(freq, t) * 0.6 + sine_wave(freq * 2, t) * 0.2) * amp
        samples.append(s)
    return samples


def gen_bomb():
    """Bomb placement beep."""
    duration = 0.15
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 440
        amp = 0.4 * (1.0 - progress * 0.5)
        # Two quick beeps
        if progress < 0.4 or (0.5 < progress < 0.9):
            s = square_wave(freq, t) * amp
        else:
            s = 0.0
        samples.append(s)
    return samples


def gen_stun():
    """Ouch/stun - descending warble."""
    duration = 0.25
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 500 - 300 * progress
        wobble = math.sin(t * 30) * 50
        amp = 0.55 * (1.0 - progress * 0.8)
        s = square_wave(freq + wobble, t) * amp
        samples.append(s)
    return samples


def gen_combo():
    """Combo match sound - bright rising chord."""
    duration = 0.25
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        amp = 0.5 * (1.0 - progress * 0.6)
        s = (sine_wave(880, t) * 0.3 + 
             sine_wave(1100, t) * 0.3 +
             triangle_wave(1320, t) * 0.2) * amp
        samples.append(s)
    return samples


def gen_line_clear():
    """Full line clear - satisfying descending sweep."""
    duration = 0.4
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 1200 - 800 * progress
        amp = 0.5 * (1.0 - progress * 0.5)
        s = (triangle_wave(freq, t) * 0.5 + 
             sine_wave(freq * 0.5, t) * 0.3 +
             noise() * 0.05) * amp
        samples.append(s)
    return samples


def gen_game_over():
    """Game over jingle - descending sad notes."""
    duration = 0.8
    samples = []
    n = int(SAMPLE_RATE * duration)
    notes = [440, 392, 349, 330, 262]  # A4, G4, F4, E4, C4
    note_dur = duration / len(notes)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        note_idx = min(int(t / note_dur), len(notes) - 1)
        freq = notes[note_idx]
        amp = 0.5 * (1.0 - progress * 0.4)
        # Slight gap between notes
        in_note = (t % note_dur) / note_dur
        if in_note > 0.9:
            amp *= 0.1
        s = (triangle_wave(freq, t) * 0.5 + sine_wave(freq, t) * 0.4) * amp
        samples.append(s)
    return samples


def gen_menu_move():
    """Short click for menu navigation."""
    duration = 0.05
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 800
        amp = 0.3 * (1.0 - progress)
        s = square_wave(freq, t) * amp
        samples.append(s)
    return samples


def gen_menu_select():
    """Confirmation beep for menu selection."""
    duration = 0.12
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 600 + 400 * progress
        amp = 0.4 * (1.0 - progress * 0.5)
        s = triangle_wave(freq, t) * amp
        samples.append(s)
    return samples


def gen_helmet():
    """Helmet/powerup active notification."""
    duration = 0.2
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 660 + 220 * math.sin(progress * math.pi * 4)
        amp = 0.4 * (1.0 - progress * 0.3)
        s = sine_wave(freq, t) * amp
        samples.append(s)
    return samples


def main():
    print("Generating retro WAV sound effects...")
    
    generators = {
        'jump.ogg': gen_jump,
        'super_jump.ogg': gen_super_jump,
        'push.ogg': gen_push,
        'land.ogg': gen_land,
        'explode.ogg': gen_explode,
        'powerup.ogg': gen_powerup,
        'bomb.ogg': gen_bomb,
        'stun.ogg': gen_stun,
        'combo.ogg': gen_combo,
        'line_clear.ogg': gen_line_clear,
        'game_over.ogg': gen_game_over,
        'menu_move.ogg': gen_menu_move,
        'menu_select.ogg': gen_menu_select,
        'helmet.ogg': gen_helmet,
    }
    
    for filename, gen_func in generators.items():
        samples = gen_func()
        write_ogg(filename, samples)
    
    print(f"\nDone! {len(generators)} sound effects created in assets/sounds/")


if __name__ == '__main__':
    main()
