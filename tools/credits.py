import numpy as np
from PIL import Image, ImageDraw, ImageFont

LINES = ["Перевод выполнил Mr.President  ·  Порт перевода сделал Risaro (t.me/lik1sa)", "Специально для phc.lokilab.ru  ·  порты PS Vita"]
FONT = "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"


def fit(text, size, w):
    font = ImageFont.truetype(FONT, size)
    while font.getlength(text) > w * 0.97 and size > 8:
        size -= 1
        font = ImageFont.truetype(FONT, size)
    return font


def add_credits(img, scale=0.76):
    w, h = img.size
    band = int(h * (1 - scale))
    logo = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(logo, ((w - logo.width) // 2, 0))
    row = band // len(LINES)
    size = min(fit(t, max(10, int(row * 0.72)), w).size for t in LINES)
    font = ImageFont.truetype(FONT, size)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for k, text in enumerate(LINES):
        tw = font.getlength(text)
        y = h - band + k * row + (row - size) // 2 - 1
        d.text(((w - tw) / 2, y), text, font=font, fill=(255, 255, 255, 255), stroke_width=max(1, size // 10), stroke_fill=(0, 0, 0, 255))
    arr = np.array(layer).astype(np.float32)
    arr[..., 3] *= 128 / 255
    layer = Image.fromarray(arr.astype(np.uint8), "RGBA")
    out.alpha_composite(layer)
    return out
