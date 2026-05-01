"""Generate arcade-style MIDI music at different tempos for Stack Attack.
Writes raw MIDI bytes - no external libraries needed.
Creates 5 tempo levels that increase from relaxed to frantic."""

import struct
import os

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

def var_len(value):
    """Encode a variable-length quantity for MIDI."""
    result = []
    result.append(value & 0x7F)
    value >>= 7
    while value:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.reverse()
    return bytes(result)

def note_on(channel, note, velocity, delta=0):
    return var_len(delta) + bytes([0x90 | channel, note, velocity])

def note_off(channel, note, velocity=0, delta=0):
    return var_len(delta) + bytes([0x80 | channel, note, velocity])

def program_change(channel, program, delta=0):
    return var_len(delta) + bytes([0xC0 | channel, program])

def control_change(channel, controller, value, delta=0):
    return var_len(delta) + bytes([0xB0 | channel, controller, value])

def set_tempo(bpm, delta=0):
    """Meta event for tempo (microseconds per beat)."""
    uspb = int(60_000_000 / bpm)
    return var_len(delta) + b'\xFF\x51\x03' + struct.pack('>I', uspb)[1:]

def end_of_track(delta=0):
    return var_len(delta) + b'\xFF\x2F\x00'

def build_track(events):
    """Wrap track events in an MTrk chunk."""
    data = b''.join(events)
    return b'Mtrk' + struct.pack('>I', len(data)) + data

def build_midi(tracks, ticks_per_beat=480):
    """Build a complete MIDI file (format 1)."""
    header = b'MThd' + struct.pack('>IHhH', 6, 1, len(tracks), ticks_per_beat)
    return header + b''.join(tracks)


def generate_gameplay_midi(bpm, filename):
    """Generate an arcade-style looping track at the given BPM.
    
    The melody is inspired by classic mobile arcade games:
    - Lead melody on channel 0 (Square wave / Synth Lead)
    - Bass line on channel 1 (Synth Bass)
    - Percussion on channel 9 (GM drums)
    """
    TPB = 480  # ticks per beat
    Q = TPB       # quarter note
    E = TPB // 2  # eighth note
    S = TPB // 4  # sixteenth note
    
    # ========================
    # TRACK 0: Tempo + Metadata
    # ========================
    meta_events = [
        set_tempo(bpm),
        end_of_track()
    ]
    track0 = build_track(meta_events)
    
    # ========================
    # TRACK 1: Lead Melody (Channel 0)
    # Synth Lead 1 (Square) = Program 80
    # ========================
    lead_events = []
    lead_events.append(program_change(0, 80))  # Synth Lead (Square)
    lead_events.append(control_change(0, 7, 100))  # Volume
    
    # Catchy arcade melody - 4 bars repeated with variation
    # Key of C minor for that intense arcade feel
    # C4=60, Eb4=63, F4=65, G4=67, Ab4=68, Bb4=70, C5=72
    
    def add_note(events, note, duration, velocity=90, gap=0):
        """Add a note with given duration and optional gap after."""
        events.append(note_on(0, note, velocity))
        events.append(note_off(0, note, 0, duration - gap))
        if gap > 0:
            # Need a silent gap - we just add delta to next event
            pass  # The gap will be the delta of the next note_on
    
    # --- Bar 1: Rising motif ---
    melody_bar1 = [
        (60, E, 95),   # C4
        (63, E, 85),   # Eb4
        (65, E, 90),   # F4
        (67, E, 95),   # G4
        (68, S, 80),   # Ab4
        (67, S, 75),   # G4
        (65, E, 85),   # F4
        (63, E, 80),   # Eb4
    ]
    
    # --- Bar 2: Peak and descent ---
    melody_bar2 = [
        (72, E, 100),  # C5
        (70, E, 90),   # Bb4
        (68, E, 85),   # Ab4
        (67, Q, 95),   # G4 (longer)
        (65, S, 80),   # F4
        (63, S, 75),   # Eb4
    ]
    
    # --- Bar 3: Syncopated rhythm ---
    melody_bar3 = [
        (60, S, 90),   # C4
        (60, S, 70),   # C4 (ghost)
        (63, E, 85),   # Eb4
        (67, E, 95),   # G4
        (65, S, 80),   # F4
        (63, S, 75),   # Eb4
        (60, E, 90),   # C4
        (67, E, 95),   # G4
        (72, E, 100),  # C5
    ]
    
    # --- Bar 4: Resolution ---
    melody_bar4 = [
        (70, E, 95),   # Bb4
        (68, E, 85),   # Ab4
        (67, E, 90),   # G4
        (65, E, 80),   # F4
        (63, Q, 95),   # Eb4 (longer)
        (60, Q, 100),  # C4 (resolution)
    ]
    
    # --- Bars 5-8: Variation (higher energy) ---
    melody_bar5 = [
        (72, S, 100),  # C5
        (72, S, 75),   # C5
        (75, E, 95),   # Eb5
        (77, E, 100),  # F5
        (79, E, 100),  # G5
        (80, S, 90),   # Ab5
        (79, S, 85),   # G5
        (77, E, 90),   # F5
        (75, E, 85),   # Eb5
    ]
    
    melody_bar6 = [
        (84, E, 105),  # C6
        (82, E, 95),   # Bb5
        (80, E, 90),   # Ab5
        (79, Q, 100),  # G5
        (77, S, 85),   # F5
        (75, S, 80),   # Eb5
    ]
    
    melody_bar7 = [
        (72, S, 95),   # C5
        (72, S, 75),   # C5
        (75, E, 90),   # Eb5
        (79, E, 100),  # G5
        (77, S, 85),   # F5
        (75, S, 80),   # Eb5
        (72, E, 95),   # C5
        (79, E, 100),  # G5
        (84, E, 105),  # C6
    ]
    
    melody_bar8 = [
        (82, E, 100),  # Bb5
        (80, E, 90),   # Ab5
        (79, E, 95),   # G5
        (77, E, 85),   # F5
        (75, Q, 100),  # Eb5
        (72, Q, 105),  # C5
    ]
    
    all_bars = [
        melody_bar1, melody_bar2, melody_bar3, melody_bar4,
        melody_bar5, melody_bar6, melody_bar7, melody_bar8,
    ]
    
    for bar in all_bars:
        for note, dur, vel in bar:
            lead_events.append(note_on(0, note, vel))
            lead_events.append(note_off(0, note, 0, dur))
    
    lead_events.append(end_of_track())
    track1 = build_track(lead_events)
    
    # ========================
    # TRACK 2: Bass Line (Channel 1)
    # Synth Bass 1 = Program 38
    # ========================
    bass_events = []
    bass_events.append(program_change(1, 38))  # Synth Bass
    bass_events.append(control_change(1, 7, 90))  # Volume
    
    # Simple driving bass - root notes with octave pumps
    # Each bar is 4 beats (4 * Q ticks)
    bass_pattern = [
        # Bar 1-2: C minor
        (36, Q), (36, E), (48, E),  # C2, C2, C3
        (36, Q), (43, E), (48, E),  # C2, G2, C3
        (36, Q), (36, E), (48, E),
        (43, Q), (41, E), (39, E),  # G2, F2, Eb2
        # Bar 3-4: Movement
        (36, Q), (36, E), (48, E),
        (39, Q), (39, E), (51, E),  # Eb2, Eb2, Eb3
        (41, Q), (41, E), (53, E),  # F2, F2, F3
        (43, Q), (36, E), (48, E),  # G2, C2, C3
        # Bar 5-8: Same pattern octave up for energy
        (48, Q), (48, E), (60, E),  # C3, C3, C4
        (48, Q), (55, E), (60, E),  # C3, G3, C4
        (48, Q), (48, E), (60, E),
        (55, Q), (53, E), (51, E),  # G3, F3, Eb3
        (48, Q), (48, E), (60, E),
        (51, Q), (51, E), (63, E),  # Eb3, Eb3, Eb4
        (53, Q), (53, E), (65, E),  # F3, F3, F4
        (55, Q), (48, E), (60, E),  # G3, C3, C4
    ]
    
    for note, dur in bass_pattern:
        bass_events.append(note_on(1, note, 80))
        bass_events.append(note_off(1, note, 0, dur))
    
    bass_events.append(end_of_track())
    track2 = build_track(bass_events)
    
    # ========================
    # TRACK 3: Drums (Channel 9)
    # GM Percussion: Kick=36, Snare=38, HiHat=42, OpenHH=46
    # ========================
    drum_events = []
    drum_events.append(control_change(9, 7, 95))  # Volume
    
    KICK = 36
    SNARE = 38
    HIHAT_C = 42  # Closed hi-hat
    HIHAT_O = 46  # Open hi-hat
    
    # 8 bars of drums
    for bar in range(8):
        for beat in range(4):
            # Hi-hat on every eighth note
            drum_events.append(note_on(9, HIHAT_C, 70))
            drum_events.append(note_off(9, HIHAT_C, 0, S))
            
            if beat % 2 == 0:
                # Hi-hat + kick on beats 1 and 3
                drum_events.append(note_on(9, KICK, 100))
                drum_events.append(note_on(9, HIHAT_C, 65, 0))
                drum_events.append(note_off(9, KICK, 0, S))
                drum_events.append(note_off(9, HIHAT_C, 0, 0))
            else:
                # Hi-hat + snare on beats 2 and 4
                drum_events.append(note_on(9, SNARE, 95))
                drum_events.append(note_on(9, HIHAT_O if beat == 3 else HIHAT_C, 65, 0))
                drum_events.append(note_off(9, SNARE, 0, S))
                drum_events.append(note_off(9, HIHAT_O if beat == 3 else HIHAT_C, 0, 0))
    
    drum_events.append(end_of_track())
    track3 = build_track(drum_events)
    
    # Build the complete MIDI
    midi_data = build_midi([track0, track1, track2, track3], TPB)
    
    filepath = os.path.join(ASSETS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(midi_data)
    print(f"  Generated: {filename} ({bpm} BPM, {len(midi_data)} bytes)")


# Generate 5 tempo levels
TEMPOS = [
    (100, "gameplay_1.mid"),  # Relaxed start
    (120, "gameplay_2.mid"),  # Getting warmer
    (140, "gameplay_3.mid"),  # Medium intensity
    (165, "gameplay_4.mid"),  # Getting frantic
    (195, "gameplay_5.mid"),  # Maximum chaos
]

print("Generating Stack Attack gameplay music...")
for bpm, filename in TEMPOS:
    generate_gameplay_midi(bpm, filename)

print(f"\nDone! {len(TEMPOS)} tracks generated in: {ASSETS_DIR}")
