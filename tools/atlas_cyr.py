import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from cyrmap import SLOTS
from vtex import decode, encode

FONT = "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"
NARROW = 1.0


def narrow(cell, k, pixel):
    a = cell[..., 3]
    xs = np.nonzero(a.max(0) > 8)[0]
    if not len(xs):
        return cell
    x0, x1 = xs.min(), xs.max() + 1
    gw = x1 - x0
    nw = max(1, round(gw * k))
    part = cell[:, x0:x1]
    chans = [np.array(Image.fromarray(part[..., c]).resize((nw, part.shape[0]), Image.LANCZOS)) for c in range(4)]
    g = np.stack(chans, -1)
    if pixel:
        g[..., 3] = np.where(g[..., 3] > 110, 255, 0)
    res = np.zeros_like(cell)
    ox = x0 + (gw - nw) // 2
    res[:, ox : ox + nw] = g
    return res


def cell_of(ch):
    c = ord(ch) - 0x20
    return c % 32, c // 32


def build(vita, styled=False, pixel=False):
    img = np.array(decode(vita)).astype(np.float32)
    h, w = img.shape[:2]
    cw, chh = w // 32, h // 3
    alpha = img[..., 3]
    hx, hy = cell_of("H")
    hcell = alpha[hy * chh : (hy + 1) * chh, hx * cw : (hx + 1) * cw]
    ys, xs = np.nonzero(hcell > 64)
    top, bot = ys.min(), ys.max() + 1
    left = xs.min()
    widths = []
    for L in "ABCDEHKMNOPRSTUX":
        x, y = cell_of(L)
        c = alpha[y * chh : (y + 1) * chh, x * cw : (x + 1) * cw]
        xx = np.nonzero(c.max(0) > 64)[0]
        if len(xx):
            widths.append(xx.max() - xx.min() + 1)
    gw = int(np.median(widths))
    mx, my = cell_of("M")
    mcol = np.nonzero(alpha[my * chh : (my + 1) * chh, mx * cw : (mx + 1) * cw].max(0) > 64)[0]
    mw = mcol.max() - mcol.min() + 1
    stroke_ref = np.mean([(r > 64).sum() for r in hcell[top:bot].T if (r > 64).any()])
    out = img.copy()
    big = 8
    font = ImageFont.truetype(FONT, int((bot - top) * big * 1.38))
    for ch, code in SLOTS.items():
        x0, y0 = cell_of(code)
        x0, y0 = x0 * cw, y0 * chh
        canvas = Image.new("L", (font.size * 2, font.size * 2), 0)
        ImageDraw.Draw(canvas).text((font.size // 2, font.size // 4), ch, font=font, fill=255)
        bb = canvas.getbbox()
        g = canvas.crop(bb)
        cap = (bot - top) * big
        scale = cap / (bb[3] - bb[1]) if ch not in "ЦЩД" else None
        if ch in "ЦЩД":
            ref = Image.new("L", (font.size * 2, font.size * 2), 0)
            ImageDraw.Draw(ref).text((font.size // 2, font.size // 4), "Н", font=font, fill=255)
            rb = ref.getbbox()
            scale = cap / (rb[3] - rb[1])
            desc = (bb[3] - bb[1]) * scale - cap
        else:
            desc = 0
        tw = big * (mw if ch in "ЖШЩЮЫ" else gw * 0.9 if ch in "ГЧУЭЬЪ" else gw)
        g = g.resize((max(1, int(tw)), max(1, int((bb[3] - bb[1]) * scale))), Image.LANCZOS)
        g = g.resize((max(1, g.width // big), max(1, g.height // big)), Image.LANCZOS)
        if g.width > cw - 2:
            g = g.resize((cw - 2, g.height), Image.LANCZOS)
        m = np.array(g).astype(np.float32)
        if stroke_ref > 4:
            m = np.array(Image.fromarray(m.astype(np.uint8)).filter(ImageFilter.MaxFilter(3))).astype(np.float32) * 0.5 + m * 0.5
        if pixel:
            m = np.where(m > 110, 255, 0).astype(np.float32)
        cell = np.zeros((chh, cw, 4), np.float32)
        ox = left if g.width <= cw - left - 1 else max(0, (cw - g.width) // 2)
        oy = top
        hh = min(g.height, chh - oy)
        ww = min(g.width, cw - ox)
        if styled:
            fill = np.percentile(img[hy * chh : (hy + 1) * chh, hx * cw : (hx + 1) * cw][hcell > 200][:, :3], 95, axis=0)
            mask = np.zeros((chh, cw), np.float32)
            mask[oy : oy + hh, ox : ox + ww] = m[:hh, :ww]
            ring = np.array(Image.fromarray(mask.astype(np.uint8)).filter(ImageFilter.MaxFilter(3))).astype(np.float32)
            cell[..., 3] = np.maximum(ring, mask)
            inner = mask / 255
            cell[..., :3] = fill * inner[..., None]
        else:
            cell[..., :3] = 255
            cell[oy : oy + hh, ox : ox + ww, 3] = m[:hh, :ww]
        out[y0 : y0 + chh, x0 : x0 + cw] = cell
    for code in SLOTS.values():
        x0, y0 = cell_of(code)
        x0, y0 = x0 * cw, y0 * chh
        out[y0 : y0 + chh, x0 : x0 + cw] = narrow(out[y0 : y0 + chh, x0 : x0 + cw], NARROW, pixel)
    res = out.copy()
    res[..., 3] = np.round(res[..., 3] * 128 / 255)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA"), encode(Image.fromarray(np.clip(res, 0, 255).astype(np.uint8), "RGBA"), vita)
