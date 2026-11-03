import gzip
import io
import struct
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EBOOT = ROOT / "dump/elf/eboot.bin.elf"
PC_FONT = ROOT / "pc-rus/font/font.bin"
GZ_OFFSET = 0xA6855C
GZ_SIZE = 723223
SIZE_FIELD = GZ_OFFSET - 4


def parse(blob):
    cw, ch, extra, toc_off, count = struct.unpack("<5I", blob[4:24])
    toc = [struct.unpack("<II", blob[toc_off + i * 8 : toc_off + i * 8 + 8]) for i in range(count)]
    return (cw, ch, extra, toc_off), toc


def glyph(blob, off):
    w, h, x, y, adv = struct.unpack("<BBbbB", blob[off : off + 5])
    pix = np.frombuffer(blob, np.uint8, w * h, off + 5).reshape(h, w) if w and h else np.zeros((0, 0), np.uint8)
    return w, h, x, y, adv, pix


def ink_box(a):
    ys, xs = np.nonzero(a > 16)
    if len(ys) == 0:
        return None
    return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1


def lookup(toc):
    d = {}
    for c, o in toc:
        d.setdefault(c, o)
    return d


def metrics(blob, table, cp):
    w, h, x, y, adv, pix = glyph(blob, table[cp])
    t, b, l, r = ink_box(pix)
    return y + t, y + b


def convert(pc, pc_table, cp, sx, sy, pc_base, v_base):
    w, h, x, y, adv, pix = glyph(pc, pc_table[cp])
    box = ink_box(pix) if w and h else None
    if box is None:
        return bytes([0, 1, 0, 25, 9, 0])
    t, b, l, r = box
    src = pix[t:b, l:r]
    nw = max(1, round((r - l) * sx))
    nh = max(1, round((b - t) * sy))
    img = Image.fromarray(src, "L").resize((nw, nh), Image.LANCZOS)
    top = round((y + t - pc_base) * sy) + v_base
    return struct.pack("<BBbbB", nw, nh, 1, top, nw + 2) + img.tobytes()


def build():
    eboot = EBOOT.read_bytes()
    raw = gzip.decompress(eboot[GZ_OFFSET : GZ_OFFSET + GZ_SIZE])
    pc = PC_FONT.read_bytes()
    (cw, ch, extra, toc_off), vt = parse(raw)
    _, pt = parse(pc)
    vl = lookup(vt)
    pl = lookup(pt)
    v_cap_top, v_base = metrics(raw, vl, 0x48)
    p_cap_top, p_base = metrics(pc, pl, 0x48)
    p_cyr_top, p_cyr_base = metrics(pc, pl, 0x043D)
    v_x_top, v_x_base = metrics(raw, vl, 0x78)
    sy = (v_x_base - v_x_top) / (p_cyr_base - p_cyr_top)
    sx = sy * 0.92
    base = [(c, raw[o : o + 5 + raw[o] * raw[o + 1]]) for c, o in vt]
    existing = {c for c, _ in base}
    added = []
    for c, _ in pt:
        if (0x400 <= c <= 0x4FF) and c not in existing and c not in [a for a, _ in added]:
            added.append((c, convert(pc, pl, c, sx, sy, p_cyr_base, v_base)))
    kanji = [c for c, _ in base if 0x4E00 <= c <= 0x9FFF]
    drop = 0
    while True:
        gone = set(kanji[len(kanji) - drop :]) if drop else set()
        glyphs = sorted([g for g in base if g[0] not in gone] + added, key=lambda g: g[0])
        new_raw, gz_blob = pack(raw[:toc_off], cw, ch, extra, toc_off, glyphs)
        if len(gz_blob) <= GZ_SIZE and len(new_raw) <= len(raw):
            break
        drop += 8
    print(f"font glyphs {len(vt)} -> {len(glyphs)}, added {len(added)}, dropped kanji {drop}, raw {len(new_raw)}, gz {len(gz_blob)}/{GZ_SIZE}")
    return new_raw, gz_blob


def pack(head, cw, ch, extra, toc_off, glyphs):
    head = head[:4] + struct.pack("<5I", cw, ch, extra, toc_off, len(glyphs))
    data_off = toc_off + 8 * len(glyphs)
    toc = bytearray()
    body = bytearray()
    for c, g in glyphs:
        toc += struct.pack("<II", c, data_off + len(body))
        body += g
    new_raw = bytes(head) + bytes(toc) + bytes(body)
    buf = io.BytesIO()
    with gzip.GzipFile(filename="MGS_Font.raw", mode="wb", fileobj=buf, compresslevel=9, mtime=0) as gz:
        gz.write(new_raw)
    return new_raw, buf.getvalue()


if __name__ == "__main__":
    raw, _ = build()
    (ROOT / "tools/plugin/font.raw").write_bytes(raw)
