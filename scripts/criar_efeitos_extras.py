# -*- coding: utf-8 -*-
"""Cria PNGs transparentes extras para os overframes do canal Soninho."""
from __future__ import annotations
import math
import sys
import io
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
SAIDA = ROOT / "efeitos"
SAIDA.mkdir(parents=True, exist_ok=True)
S = 4  # superamostragem


def salvar(img: Image.Image, nome: str) -> None:
    img = img.resize((img.width // S, img.height // S), Image.LANCZOS)
    img.save(SAIDA / nome)
    print("CRIADO:", nome, img.size)


def cometa() -> None:
    w, h = 180 * S, 70 * S
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w * 0.86, h * 0.5
    # cauda inclinada: distancia perpendicular a reta do cometa
    ang = math.radians(-12)
    dx, dy = xx - cx, yy - cy
    along = dx * math.cos(ang) + dy * math.sin(ang)
    perp = -dx * math.sin(ang) + dy * math.cos(ang)
    alpha = np.where(along < 0, np.exp(along / (w * 0.26)) * np.exp(-(perp ** 2) / (2 * (h * 0.10) ** 2)), 0)
    cabeca = np.exp(-((dx ** 2 + dy ** 2) / (2 * (h * 0.085) ** 2)))
    alpha = np.clip(alpha * 0.75 + cabeca, 0, 1)
    rgb = np.zeros((h, w, 4), dtype=np.uint8)
    rgb[..., 0] = 255
    rgb[..., 1] = 236
    rgb[..., 2] = 190
    rgb[..., 3] = (alpha * 255).astype(np.uint8)
    salvar(Image.fromarray(rgb, "RGBA"), "cometa.png")


def solzinho() -> None:
    size = 150 * S
    yy, xx = np.mgrid[0:size, 0:size]
    c = size / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    ang = np.arctan2(yy - c, xx - c)
    raios = 0.5 + 0.5 * np.cos(ang * 10)
    brilho = np.clip(1 - r / (c * 0.55), 0, 1) ** 2 * 0.75
    brilho += np.clip(1 - r / (c * 0.95), 0, 1) ** 4 * raios * 0.45
    rgb = np.zeros((size, size, 4), dtype=np.uint8)
    rgb[..., 0] = 255
    rgb[..., 1] = 224
    rgb[..., 2] = 158
    rgb[..., 3] = (np.clip(brilho, 0, 1) * 200).astype(np.uint8)
    salvar(Image.fromarray(rgb, "RGBA"), "solzinho.png")


def coracao_extras() -> None:
    # versao maior e mais suave do coracao, para variar tamanho
    size = 80 * S
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size // 2
    r = int(size * 0.24)
    d.ellipse([c - r, c - r - int(r * 0.3), c, c + int(r * 0.45)], fill=(255, 138, 160, 190))
    d.ellipse([c, c - r - int(r * 0.3), c + r, c + int(r * 0.45)], fill=(255, 138, 160, 190))
    d.polygon([(c - r - 2, c), (c + r + 2, c), (c, c + int(r * 1.8))], fill=(255, 138, 160, 190))
    salvar(img, "coracao_suave.png")


if __name__ == "__main__":
    cometa(); solzinho(); coracao_extras()
    print("PASTA:", SAIDA)
