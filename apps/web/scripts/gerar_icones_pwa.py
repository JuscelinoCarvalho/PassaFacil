#!/usr/bin/env python3
"""Gera os ícones do PWA (instalável no celular) a partir da marca do app.

Marca: monograma "PF" sobre gradiente roxo (#8970f1 -> #5f40dd), o mesmo da
`.brand-mark` do globals.css. Gera versões normais (com margem) e "maskable"
(preenchendo a tela toda, pro Android recortar em círculo/squircle).

Uso: python3 scripts/gerar_icones_pwa.py
Saída: apps/web/public/icons/*.png
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "public", "icons")
os.makedirs(OUT, exist_ok=True)

TOP = (137, 112, 241)   # #8970f1
BOT = (95, 64, 221)     # #5f40dd
WHITE = (255, 255, 255)


def _font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _gradient(size):
    """Gradiente vertical diagonal suave (145deg-ish)."""
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            # projeção na diagonal para lembrar o linear-gradient(145deg)
            t = (x * 0.35 + y * 0.65) / size
            t = max(0.0, min(1.0, t))
            r = int(TOP[0] + (BOT[0] - TOP[0]) * t)
            g = int(TOP[1] + (BOT[1] - TOP[1]) * t)
            b = int(TOP[2] + (BOT[2] - TOP[2]) * t)
            px[x, y] = (r, g, b)
    return img


def _rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def _draw_monogram(base, size, scale=0.52):
    d = ImageDraw.Draw(base)
    txt = "PF"
    font = _font(int(size * scale))
    bbox = d.textbbox((0, 0), txt, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - w) / 2 - bbox[0]
    y = (size - h) / 2 - bbox[1]
    # leve sombra pra dar profundidade
    d.text((x + size * 0.012, y + size * 0.012), txt, font=font, fill=(0, 0, 0, 60))
    d.text((x, y), txt, font=font, fill=WHITE)


def make(size, name, maskable=False):
    grad = _gradient(size)
    if maskable:
        # preenche tudo; a "safe zone" (~80%) contém o monograma
        img = grad.convert("RGBA")
        _draw_monogram(img, size, scale=0.42)
    else:
        # cantos arredondados estilo squircle, com o gradiente
        radius = int(size * 0.22)
        mask = _rounded_mask(size, radius)
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        img.paste(grad, (0, 0), mask)
        _draw_monogram(img, size, scale=0.5)
    path = os.path.join(OUT, name)
    img.save(path, "PNG")
    print("ok", os.path.relpath(path))


if __name__ == "__main__":
    make(192, "icon-192.png")
    make(512, "icon-512.png")
    make(512, "icon-maskable-512.png", maskable=True)
    make(180, "apple-touch-icon.png")
    print("Ícones do PWA gerados em public/icons/")
