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


def write_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """Write samples (list of floats -1.0 to 1.0) to a 16-bit mono WAV file."""
    path = os.path.join(OUTPUT, filename)
    num_samples = len(samples)
    data_size = num_samples * 2
    
    with open(path, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))       # chunk size
        f.write(struct.pack('<H', 1))        # PCM
        f.write(struct.pack('<H', 1))        # mono
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))  # byte rate
        f.write(struct.pack('<H', 2))        # block align
        f.write(struct.pack('<H', 16))       # bits per sample
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for s in samples:
            s = max(-1.0, min(1.0, s))
            val = int(s * 32767)
            f.write(struct.pack('<h', val))
    
    print(f"  Created {filename} ({num_samples} samples, {num_samples/sample_rate:.2f}s)")


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
    """Short ascending chirp - classic platformer jump sound."""
    duration = 0.15
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 200 + 600 * progress  # sweep up from 200 to 800 Hz
        amp = 0.6 * (1.0 - progress * 0.7)  # fade out
        s = square_wave(freq, t) * amp * 0.5 + sine_wave(freq * 2, t) * amp * 0.3
        samples.append(s)
    return samples


def gen_super_jump():
    """Higher-pitched ascending chirp with harmonic overtone."""
    duration = 0.2
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = 300 + 1000 * progress  # sweep up higher
        amp = 0.65 * (1.0 - progress * 0.6)
        s = (square_wave(freq, t) * 0.4 + 
             sine_wave(freq * 1.5, t) * 0.3 +
             triangle_wave(freq * 2, t) * 0.2) * amp
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
        'jump.wav': gen_jump,
        'super_jump.wav': gen_super_jump,
        'push.wav': gen_push,
        'land.wav': gen_land,
        'explode.wav': gen_explode,
        'powerup.wav': gen_powerup,
        'bomb.wav': gen_bomb,
        'stun.wav': gen_stun,
        'combo.wav': gen_combo,
        'line_clear.wav': gen_line_clear,
        'game_over.wav': gen_game_over,
        'menu_move.wav': gen_menu_move,
        'menu_select.wav': gen_menu_select,
        'helmet.wav': gen_helmet,
    }
    
    for filename, gen_func in generators.items():
        samples = gen_func()
        write_wav(filename, samples)
    
    print(f"\nDone! {len(generators)} sound effects created in assets/sounds/")


if __name__ == '__main__':
    main()
