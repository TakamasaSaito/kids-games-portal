#!/usr/bin/env python3
"""Generate portal placeholder icons (pure stdlib, no external deps)."""
import struct, zlib, os

def make_png(size, top_rgb, bottom_rgb):
    def chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xffffffff
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))

    raw = bytearray()
    for y in range(size):
        t = y / max(size - 1, 1)
        r = round(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * t)
        g = round(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * t)
        b = round(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * t)
        raw += b'\x00' + bytes([r, g, b]) * size

    idat = chunk(b'IDAT', zlib.compress(bytes(raw), 6))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

if __name__ == '__main__':
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icons')
    os.makedirs(out_dir, exist_ok=True)
    # #667eea (top) → #764ba2 (bottom) — same gradient as the games
    top    = (102, 126, 234)
    bottom = (118,  75, 162)
    for size, name in [(180, 'icon-180.png'), (512, 'icon-512.png')]:
        path = os.path.join(out_dir, name)
        with open(path, 'wb') as f:
            f.write(make_png(size, top, bottom))
        print(f'Created {path}')
