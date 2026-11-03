import struct

import numpy as np
from PIL import Image

HEAD = 32
PAL = 1024


def morton_y_first(w, h):
    bx = (w - 1).bit_length()
    by = (h - 1).bit_length()
    c = min(bx, by)
    X, Y = np.meshgrid(np.arange(w), np.arange(h))
    idx = np.zeros_like(X)
    bit = 0
    for i in range(c):
        idx |= ((Y >> i) & 1) << bit
        bit += 1
        idx |= ((X >> i) & 1) << bit
        bit += 1
    idx |= ((X >> c) if bx > c else (Y >> c)) << bit
    return idx


def levels(w, h, body):
    out = []
    total = 0
    while True:
        pitch = (w + 7) & ~7
        out.append((w, h, pitch))
        total += pitch * h
        if total >= body or ((total + 63) & ~63) == body or (w == 1 and h == 1):
            break
        w, h = max(1, w // 2), max(1, h // 2)
    return out if ((total + 63) & ~63) == body or total == body else None


def is_pow2(n):
    return n & (n - 1) == 0


def swizzled(w, h):
    return is_pow2(w) and is_pow2(h)


def decode(d):
    w, h = struct.unpack("<HH", d[24:28])
    pal = np.frombuffer(d[-PAL:], np.uint8).reshape(256, 4).astype(np.float32)
    pitch = (w + 7) & ~7
    if swizzled(w, h):
        px = np.frombuffer(d, np.uint8, w * h, HEAD)[morton_y_first(w, h)]
    else:
        px = np.frombuffer(d, np.uint8, pitch * h, HEAD).reshape(h, pitch)[:, :w]
    out = pal[px]
    out[..., 3] = np.minimum(out[..., 3] * 255 / 128, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def premul_resize(img, size):
    a = np.array(img.convert("RGBA")).astype(np.float32) / 255
    a[..., :3] *= a[..., 3:4]
    chans = [Image.fromarray(a[..., i], "F").resize(size, Image.LANCZOS) for i in range(4)]
    b = np.stack([np.array(c) for c in chans], -1).clip(0, 1)
    alpha = b[..., 3:4]
    b[..., :3] = np.where(alpha > 1e-4, b[..., :3] / np.maximum(alpha, 1e-4), 0)
    return Image.fromarray((b * 255 + 0.5).astype(np.uint8), "RGBA")


def encode(img, vita):
    w, h = struct.unpack("<HH", vita[24:28])
    body = len(vita) - HEAD - PAL
    lv = levels(w, h, body)
    if lv is None:
        return None
    src = np.array(img.convert("RGBA")).astype(np.float32)
    src[..., 3] = np.minimum(src[..., 3] * 255 / 128, 255)
    base = premul_resize(Image.fromarray(src.astype(np.uint8), "RGBA"), (w, h))
    q = base.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette(rawmode="RGBA")[: 256 * 4], np.uint8).reshape(-1, 4)
    pal = np.vstack([pal, np.zeros((256 - len(pal), 4), np.uint8)])
    pal[:, 3] = (pal[:, 3].astype(int) * 128 + 127) // 255
    idx0 = np.array(q, np.uint8)
    pixels = bytearray()
    for i, (lw, lh, pitch) in enumerate(lv):
        level = idx0 if i == 0 else np.array(Image.fromarray(idx0, "L").resize((lw, lh), Image.NEAREST))
        if swizzled(w, h):
            buf = np.zeros(pitch * lh, np.uint8)
            if is_pow2(lw) and is_pow2(lh):
                flat = np.zeros(lw * lh, np.uint8)
                flat[morton_y_first(lw, lh).ravel()] = level.ravel()
                buf[: lw * lh] = flat
            pixels += buf.tobytes()
        else:
            row = np.zeros((lh, pitch), np.uint8)
            row[:, :lw] = level
            pixels += row.tobytes()
    pixels += b"\0" * (body - len(pixels))
    out = vita[:HEAD] + bytes(pixels) + pal.tobytes()
    assert len(out) == len(vita)
    return out
