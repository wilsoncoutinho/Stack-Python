import os

for name in ['jump.mmf', 'bang.mmf', 'boxland.mmf', 'cranedrp.mmf', 'ouch.mmf', 'tick.mmf']:
    path = os.path.join('assets', name)
    with open(path, 'rb') as f:
        data = f.read()
    print(f'{name}: size={len(data)} bytes, magic={data[:4]}, hex_head={data[:32].hex()}')
