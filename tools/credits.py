import numpy as np
from PIL import Image, ImageDraw, ImageFont

TEXT = "Перевод выполнил Mr.President  ·  Порт перевода сделал Risaro (t.me/lik1sa)"
FONT = "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"


def add_credits(img, scale=0.86):
    w, h = img.size
    band = int(h * (1 - scale))
    logo = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(logo, ((w - logo.width) // 2, 0))
    size = max(10, int(band * 0.62))
    font = ImageFont.truetype(FONT, size)
    while font.getlength(TEXT) > w * 0.97 and size > 8:
        size -= 1
        font = ImageFont.truetype(FONT, size)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tw = font.getlength(TEXT)
    y = h - band + (band - size) // 2 - 1
    d.text(((w - tw) / 2, y), TEXT, font=font, fill=(255, 255, 255, 255), stroke_width=max(1, size // 10), stroke_fill=(0, 0, 0, 255))
    arr = np.array(layer).astype(np.float32)
    arr[..., 3] *= 128 / 255
    layer = Image.fromarray(arr.astype(np.uint8), "RGBA")
    out.alpha_composite(layer)
    return out
