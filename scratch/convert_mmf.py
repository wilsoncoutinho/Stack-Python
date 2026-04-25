"""
MMF (SMAF) to MIDI converter for Stack Attack sound effects.
SMAF files contain MA-2/MA-3 sequence data inside chunks.
We parse the SMAF container to extract the score track data,
then convert the note events to standard MIDI format.
"""
import os
import struct

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
OUTPUT = os.path.join(ASSETS, "sounds")
os.makedirs(OUTPUT, exist_ok=True)


def read_chunk(data, offset):
    """Read a SMAF chunk: 4-byte type + 4-byte big-endian size + payload."""
    if offset + 8 > len(data):
        return None, None, offset
    chunk_type = data[offset:offset+4].decode('ascii', errors='replace')
    chunk_size = struct.unpack('>I', data[offset+4:offset+8])[0]
    payload = data[offset+8:offset+8+chunk_size]
    return chunk_type, payload, offset + 8 + chunk_size


def parse_smaf_chunks(data):
    """Parse top-level SMAF chunks."""
    chunks = {}
    offset = 0
    while offset < len(data):
        ctype, payload, offset = read_chunk(data, offset)
        if ctype is None:
            break
        chunks[ctype] = payload
    return chunks


def find_sub_chunks(data):
    """Find all sub-chunks in a chunk payload."""
    chunks = []
    offset = 0
    while offset + 8 <= len(data):
        ctype = data[offset:offset+4].decode('ascii', errors='replace')
        csize = struct.unpack('>I', data[offset+4:offset+8])[0]
        payload = data[offset+8:offset+8+csize]
        chunks.append((ctype, payload))
        offset += 8 + csize
    return chunks


def smaf_to_midi(smaf_data):
    """
    Convert SMAF/MMF data to a simple MIDI file.
    SMAF score tracks (MTR*) contain note-on/off events we can map to MIDI.
    """
    # Parse the outer MMMD container
    if smaf_data[:4] != b'MMMD':
        return None
    
    total_size = struct.unpack('>I', smaf_data[4:8])[0]
    inner = smaf_data[8:8+total_size]
    
    top_chunks = find_sub_chunks(inner)
    
    # Look for score track chunks (OPDA contains the actual sequence data)
    midi_events = []
    timebase = 120  # default SMAF timebase
    
    for ctype, payload in top_chunks:
        if ctype == 'OPDA':
            # OPDA contains sub-chunks with the actual music data
            sub_chunks = find_sub_chunks(payload)
            for stype, spayload in sub_chunks:
                if stype.startswith('MTR') or stype.startswith('Mtr'):
                    # Score track data - parse MA-2 sequence events
                    events = parse_ma2_track(spayload, timebase)
                    midi_events.extend(events)
        elif ctype.startswith('MTR') or ctype.startswith('Mtr'):
            events = parse_ma2_track(payload, timebase)
            midi_events.extend(events)
    
    if not midi_events:
        # Try brute force: scan for note-like patterns
        midi_events = extract_notes_bruteforce(inner, timebase)
    
    if not midi_events:
        return None
    
    return build_midi(midi_events, timebase)


def parse_ma2_track(data, timebase):
    """Parse MA-2/MA-3 sequence track data into note events."""
    events = []
    offset = 0
    current_time = 0
    
    while offset < len(data):
        byte = data[offset]
        
        # Duration/rest bytes
        if byte == 0x00:
            offset += 1
            continue
        
        # Note on: 0x9n where n=channel
        if (byte & 0xF0) == 0x90 and offset + 2 < len(data):
            channel = byte & 0x0F
            note = data[offset + 1]
            velocity = data[offset + 2] if offset + 2 < len(data) else 100
            if 0 <= note <= 127:
                events.append((current_time, 'note_on', channel, note, min(127, velocity)))
                events.append((current_time + timebase // 4, 'note_off', channel, note, 0))
            offset += 3
            current_time += timebase // 8
            continue
        
        # Note off: 0x8n
        if (byte & 0xF0) == 0x80 and offset + 2 < len(data):
            channel = byte & 0x0F
            note = data[offset + 1]
            events.append((current_time, 'note_off', channel, note, 0))
            offset += 3
            continue
        
        # Program change: 0xCn
        if (byte & 0xF0) == 0xC0 and offset + 1 < len(data):
            offset += 2
            continue
        
        # Control change: 0xBn
        if (byte & 0xF0) == 0xB0 and offset + 2 < len(data):
            offset += 3
            continue
        
        # Delta time (variable length)
        if byte & 0x80 == 0:
            current_time += byte
            offset += 1
            continue
        
        offset += 1
    
    return events


def extract_notes_bruteforce(data, timebase):
    """Brute-force scan for MIDI-like note events in binary data."""
    events = []
    current_time = 0
    
    for i in range(len(data) - 2):
        byte = data[i]
        if (byte & 0xF0) == 0x90:  # note on
            note = data[i + 1]
            vel = data[i + 2]
            if 20 <= note <= 108 and 1 <= vel <= 127:
                events.append((current_time, 'note_on', byte & 0x0F, note, vel))
                events.append((current_time + timebase // 2, 'note_off', byte & 0x0F, note, 0))
                current_time += timebase // 4
    
    return events


def write_variable_length(value):
    """Encode a value as MIDI variable-length quantity."""
    result = []
    result.append(value & 0x7F)
    value >>= 7
    while value > 0:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.reverse()
    return bytes(result)


def build_midi(events, timebase=120):
    """Build a standard MIDI file from a list of events."""
    if not events:
        return None
    
    events.sort(key=lambda e: e[0])
    
    # Build track data
    track_data = bytearray()
    last_time = 0
    
    for event in events:
        time, etype, channel, note, velocity = event
        delta = max(0, time - last_time)
        last_time = time
        
        track_data.extend(write_variable_length(delta))
        
        if etype == 'note_on':
            track_data.extend([0x90 | (channel & 0x0F), note & 0x7F, velocity & 0x7F])
        elif etype == 'note_off':
            track_data.extend([0x80 | (channel & 0x0F), note & 0x7F, 0])
    
    # End of track
    track_data.extend(write_variable_length(0))
    track_data.extend([0xFF, 0x2F, 0x00])
    
    # Build MIDI file
    midi = bytearray()
    # Header: MThd
    midi.extend(b'MThd')
    midi.extend(struct.pack('>I', 6))  # header size
    midi.extend(struct.pack('>HHH', 0, 1, timebase))  # format 0, 1 track, timebase
    # Track: MTrk
    midi.extend(b'MTrk')
    midi.extend(struct.pack('>I', len(track_data)))
    midi.extend(track_data)
    
    return bytes(midi)


def main():
    mmf_files = ['jump.mmf', 'bang.mmf', 'boxland.mmf', 'cranedrp.mmf', 'ouch.mmf', 'tick.mmf']
    
    for name in mmf_files:
        path = os.path.join(ASSETS, name)
        if not os.path.exists(path):
            print(f"  SKIP {name}: not found")
            continue
        
        with open(path, 'rb') as f:
            data = f.read()
        
        midi_data = smaf_to_midi(data)
        
        out_name = name.replace('.mmf', '.mid')
        out_path = os.path.join(OUTPUT, out_name)
        
        if midi_data:
            with open(out_path, 'wb') as f:
                f.write(midi_data)
            print(f"  OK {name} -> sounds/{out_name} ({len(midi_data)} bytes)")
        else:
            print(f"  FAIL {name}: could not extract MIDI data")


if __name__ == '__main__':
    main()
