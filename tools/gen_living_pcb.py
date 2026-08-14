#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère l'asset « Living PCB v0 » de DeskNode — 480x640 portrait.

BROUILLON ASSUMÉ. L'epic dn1-2 demande « une première ébauche, même
brouillonne » ; l'identité visuelle définitive est le travail de dn3-3, sur
assets préfabriqués. Ce script existe pour que l'asset soit REPRODUCTIBLE par
une seule commande depuis une source versionnée, pas pour être beau.

Deux sorties :
  --out-bin  RGB565 brut, sans en-tête, dans l'ordre d'octets demandé.
             C'est ce qui est flashé dans la partition `assets` et copié tel
             quel dans le framebuffer. 480 * 640 * 2 = 614 400 octets exactement.
  --out-png  Prévisualisation PNG, pour voir l'asset sans carte. C'est le seul
             des deux qui est COMMITÉ (le .bin est régénéré par le build).

Dépendances : bibliothèque standard seulement (zlib suffit pour écrire un PNG).
Pas de Pillow, donc pas de venv à installer, donc rien qui puisse entrer en
conflit avec le venv d'ESP-IDF.

⚠️ L'ordre d'octets par défaut est `le` (little-endian, l'ordre naturel d'un
   uint16_t sur ESP32-S3). Il a été PROUVÉ par la mire de couleurs pures de la
   story dn1-2 — pas supposé. S'il devait changer, c'est ici, et la preuve va
   dans hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md.
"""

import argparse
import math
import os
import random
import struct
import sys
import zlib

WIDTH = 480
HEIGHT = 640

# ─────────────────────────────────────────────────────────────────────────────
# Palette « Living PCB » — vert sombre de masque de soudure, cuivre, sérigraphie
# ─────────────────────────────────────────────────────────────────────────────
C_SUBSTRAT = (0x07, 0x14, 0x0E)   # fond, presque noir
C_MASQUE = (0x0C, 0x24, 0x19)     # masque de soudure
C_MASQUE_CLAIR = (0x11, 0x31, 0x22)
C_PISTE = (0x1C, 0x6E, 0x47)      # cuivre sous masque
C_PISTE_VIVE = (0x2C, 0xB0, 0x6E)  # piste « vivante », plus lumineuse
C_CUIVRE = (0xC2, 0x93, 0x2E)     # pastille / via, doré
C_CUIVRE_CLAIR = (0xE8, 0xC0, 0x5A)
C_SERIGRAPHIE = (0xD6, 0xE4, 0xDC)  # blanc cassé
C_SERIGRAPHIE_FAIBLE = (0x6E, 0x85, 0x79)
C_CORPS_CI = (0x14, 0x17, 0x16)   # corps de circuit intégré, noir mat
C_BORD_CI = (0x2A, 0x30, 0x2D)


# ─────────────────────────────────────────────────────────────────────────────
# Fonte 5x7, majuscules + chiffres + quelques signes.
# Chaque glyphe = 7 lignes de 5 bits, bit de poids fort = colonne de gauche.
# ─────────────────────────────────────────────────────────────────────────────
FONT = {
    'A': (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B': (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C': (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D': (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    'F': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    'G': (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    'H': (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I': (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111),
    'J': (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    'K': (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L': (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    'M': (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N': (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O': (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P': (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q': (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    'R': (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    'S': (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    'T': (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'W': (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    'X': (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    'Y': (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '0': (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    '1': (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2': (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111),
    '3': (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    '4': (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    '5': (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    '6': (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8': (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9': (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '-': (0, 0, 0, 0b11111, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 0b01100, 0b01100),
    '/': (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    ':': (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    '+': (0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0),
    '_': (0, 0, 0, 0, 0, 0, 0b11111),
}

GLYPH_W = 5
GLYPH_H = 7


class Canvas(object):
    """Toile RGB888. Un bytearray plat, pas de dépendance."""

    def __init__(self, width, height, fill=(0, 0, 0)):
        self.w = width
        self.h = height
        self.buf = bytearray(width * height * 3)
        if fill != (0, 0, 0):
            self.fill_rect(0, 0, width, height, fill)

    # ── primitives ──────────────────────────────────────────────────────────
    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return (self.buf[i], self.buf[i + 1], self.buf[i + 2])

    def blend(self, x, y, color, alpha):
        """alpha dans [0,1]."""
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        i = (y * self.w + x) * 3
        for k in range(3):
            old = self.buf[i + k]
            self.buf[i + k] = int(old + (color[k] - old) * alpha) & 0xFF

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def rect_outline(self, x, y, w, h, color, thickness=1):
        for t in range(thickness):
            self.fill_rect(x + t, y + t, w - 2 * t, 1, color)
            self.fill_rect(x + t, y + h - 1 - t, w - 2 * t, 1, color)
            self.fill_rect(x + t, y + t, 1, h - 2 * t, color)
            self.fill_rect(x + w - 1 - t, y + t, 1, h - 2 * t, color)

    def thick_line(self, x0, y0, x1, y1, color, width=2):
        """Segment épais, extrémités arrondies. Bresenham + disque."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = width // 2
        while True:
            self.disc(x0, y0, r, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        if r <= 0:
            self.px(cx, cy, color)
            return
        rr = r * r
        for yy in range(cy - r, cy + r + 1):
            dy2 = (yy - cy) ** 2
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + dy2 <= rr:
                    self.px(xx, yy, color)

    def ring(self, cx, cy, r_out, r_in, color):
        ro2 = r_out * r_out
        ri2 = r_in * r_in
        for yy in range(cy - r_out, cy + r_out + 1):
            dy2 = (yy - cy) ** 2
            for xx in range(cx - r_out, cx + r_out + 1):
                d2 = (xx - cx) ** 2 + dy2
                if ri2 <= d2 <= ro2:
                    self.px(xx, yy, color)

    def text(self, x, y, s, color, scale=2, spacing=1):
        """Écrit `s` en majuscules. Retourne la largeur consommée."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[' '])
            for gy in range(GLYPH_H):
                row = glyph[gy]
                for gx in range(GLYPH_W):
                    if row & (1 << (GLYPH_W - 1 - gx)):
                        self.fill_rect(cx + gx * scale, y + gy * scale,
                                       scale, scale, color)
            cx += (GLYPH_W + spacing) * scale
        return cx - x

    def text_width(self, s, scale=2, spacing=1):
        return len(s) * (GLYPH_W + spacing) * scale

    # ── sorties ─────────────────────────────────────────────────────────────
    def to_rgb565(self, byte_order='le'):
        """RGB565 : R sur les bits 15..11, G sur 10..5, B sur 4..0."""
        out = bytearray(self.w * self.h * 2)
        src = self.buf
        for i in range(self.w * self.h):
            r = src[i * 3]
            g = src[i * 3 + 1]
            b = src[i * 3 + 2]
            v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            if byte_order == 'le':
                out[i * 2] = v & 0xFF
                out[i * 2 + 1] = (v >> 8) & 0xFF
            else:
                out[i * 2] = (v >> 8) & 0xFF
                out[i * 2 + 1] = v & 0xFF
        return bytes(out)

    def to_png(self):
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)  # filtre « None »
            raw.extend(self.buf[y * stride:(y + 1) * stride])

        def chunk(tag, data):
            c = struct.pack('>I', len(data)) + tag + data
            return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

        ihdr = struct.pack('>IIBBBBB', self.w, self.h, 8, 2, 0, 0, 0)
        return (b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', ihdr)
                + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
                + chunk(b'IEND', b''))


# ─────────────────────────────────────────────────────────────────────────────
# Le dessin
# ─────────────────────────────────────────────────────────────────────────────

def draw_substrate(c, rng):
    """Fond : masque de soudure + grain, pour que ce ne soit pas un aplat."""
    c.fill_rect(0, 0, c.w, c.h, C_MASQUE)
    # Grain : un pixel sur 7, éclairci ou assombri de peu.
    for i in range(0, c.w * c.h, 7):
        idx = (i + rng.randrange(7)) % (c.w * c.h)
        x = idx % c.w
        y = idx // c.w
        d = rng.randrange(-8, 9)
        r, g, b = c.get(x, y)
        c.px(x, y, (max(0, min(255, r + d)),
                    max(0, min(255, g + d)),
                    max(0, min(255, b + d))))


def draw_ground_hatch(c, x, y, w, h, step=6):
    """Plan de masse hachuré à 45°, comme sur un vrai PCB."""
    for d in range(-h, w + h, step):
        c.thick_line(x + d, y, x + d - h, y + h, C_MASQUE_CLAIR, 1)


def draw_pad(c, cx, cy, r=4):
    c.disc(cx, cy, r, C_CUIVRE)
    c.ring(cx, cy, r, r - 1, C_CUIVRE_CLAIR)
    c.disc(cx, cy, max(1, r - 3), C_SUBSTRAT)


def draw_via(c, cx, cy):
    c.disc(cx, cy, 3, C_CUIVRE)
    c.disc(cx, cy, 1, C_SUBSTRAT)


def draw_chip(c, x, y, w, h, label, pins_per_side, rng, pin_len=10):
    """Un boîtier QFP : corps sombre, broches dorées, sérigraphie, pastille 1."""
    # Broches haut / bas
    for i in range(pins_per_side):
        px = x + int((i + 0.5) * w / pins_per_side)
        c.fill_rect(px - 2, y - pin_len, 4, pin_len, C_CUIVRE)
        c.fill_rect(px - 2, y + h, 4, pin_len, C_CUIVRE)
    # Broches gauche / droite
    side = max(2, int(pins_per_side * h / w))
    for i in range(side):
        py = y + int((i + 0.5) * h / side)
        c.fill_rect(x - pin_len, py - 2, pin_len, 4, C_CUIVRE)
        c.fill_rect(x + w, py - 2, pin_len, 4, C_CUIVRE)

    c.fill_rect(x, y, w, h, C_CORPS_CI)
    c.rect_outline(x, y, w, h, C_BORD_CI, 2)
    # Pastille du coin 1 — repère d'orientation du boîtier
    c.disc(x + 12, y + 12, 5, C_SERIGRAPHIE_FAIBLE)

    scale = 2 if c.text_width(label, 3) > w - 20 else 3
    tw = c.text_width(label, scale)
    c.text(x + (w - tw) // 2, y + h // 2 - (GLYPH_H * scale) // 2,
           label, C_SERIGRAPHIE, scale)


def draw_connector(c, x, y, w, n_fingers):
    """Doigts de connecteur type carte fille."""
    fw = w // (2 * n_fingers - 1)
    for i in range(n_fingers):
        c.fill_rect(x + i * 2 * fw, y, fw, 26, C_CUIVRE)
        c.fill_rect(x + i * 2 * fw, y, fw, 4, C_CUIVRE_CLAIR)


def draw_bus(c, y, x0, x1, n, gap=4, color=C_PISTE):
    for i in range(n):
        c.thick_line(x0, y + i * gap, x1, y + i * gap, color, 2)


def build(seed=20260814):
    rng = random.Random(seed)
    c = Canvas(WIDTH, HEIGHT)
    draw_substrate(c, rng)

    # ── Plans de masse hachurés, dans les zones vides ────────────────────────
    draw_ground_hatch(c, 0, 96, WIDTH, 60)
    draw_ground_hatch(c, 0, 470, WIDTH, 70)

    # ── Réseau de pistes de fond, orthogonales et à 45° ──────────────────────
    # Dessiné AVANT le bandeau d'identité : sinon les diagonales, qui peuvent
    # remonter de 90 px, barrent le sous-titre.
    for _ in range(46):
        x = rng.randrange(8, WIDTH - 8)
        y = rng.randrange(100, HEIGHT - 40)
        segs = rng.randrange(2, 5)
        col = C_PISTE_VIVE if rng.random() < 0.18 else C_PISTE
        for _s in range(segs):
            length = rng.randrange(20, 90)
            direction = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1),
                                    (1, 1), (-1, 1), (1, -1), (-1, -1)))
            nx = x + direction[0] * length
            ny = y + direction[1] * length
            c.thick_line(x, y, nx, ny, col, 3)
            x, y = nx, ny
        if rng.random() < 0.5:
            draw_via(c, max(4, min(WIDTH - 5, x)), max(4, min(HEIGHT - 5, y)))

    # ── Bandeau haut : identité + bus horizontal ─────────────────────────────
    c.fill_rect(0, 0, WIDTH, 62, C_SUBSTRAT)
    c.text(16, 14, 'DESKNODE', C_SERIGRAPHIE, 4)
    c.text(18, 44, 'LIVING PCB V0 - P1', C_SERIGRAPHIE_FAIBLE, 2)
    c.fill_rect(0, 62, WIDTH, 2, C_PISTE_VIVE)
    draw_bus(c, 72, 0, WIDTH - 1, 4, 5, C_PISTE)

    # ── Les quatre blocs sérigraphiés ────────────────────────────────────────
    draw_chip(c, 132, 214, 216, 168, 'CPU', 10, rng)      # le gros, au centre
    draw_chip(c, 26, 118, 132, 74, 'WIFI/BT', 6, rng)     # haut gauche
    draw_chip(c, 330, 126, 124, 62, 'I2C', 5, rng)        # haut droit
    draw_chip(c, 150, 452, 180, 76, 'LVGL', 8, rng)       # bas centre

    # ── Liaisons entre blocs, en pistes vives ────────────────────────────────
    for i in range(6):
        c.thick_line(92, 192 + i * 4, 92, 240 + i * 4, C_PISTE_VIVE, 2)
        c.thick_line(92, 240 + i * 4, 132, 246 + i * 4, C_PISTE_VIVE, 2)
    for i in range(5):
        c.thick_line(392, 188 + i * 5, 392, 232 + i * 5, C_PISTE_VIVE, 2)
        c.thick_line(392, 232 + i * 5, 348, 250 + i * 5, C_PISTE_VIVE, 2)
    for i in range(8):
        c.thick_line(180 + i * 12, 382, 180 + i * 12, 452, C_PISTE_VIVE, 2)

    # ── Rangées de pastilles / composants discrets ───────────────────────────
    for i in range(12):
        draw_pad(c, 22 + i * 38, 410, 5)
    for i in range(10):
        c.fill_rect(30 + i * 42, 560, 22, 10, C_CUIVRE)
        c.fill_rect(34 + i * 42, 561, 14, 8, (0x2B, 0x2B, 0x2B))

    # ── Bandeau bas : connecteur + repères de version ────────────────────────
    draw_connector(c, 40, 596, 400, 12)
    c.text(16, 578, 'DN1-2', C_SERIGRAPHIE_FAIBLE, 2)
    c.text(WIDTH - c.text_width('480X640', 2) - 16, 578, '480X640',
           C_SERIGRAPHIE_FAIBLE, 2)

    # ── Repères d'orientation ASYMÉTRIQUES ───────────────────────────────────
    # Ils servent AC3 : sans eux, une image tournée de 180° ou en miroir passe
    # inaperçue. Chaque coin porte une marque DIFFÉRENTE.
    c.rect_outline(2, 66, 18, 18, C_SERIGRAPHIE, 2)              # HG : carré
    c.disc(WIDTH - 12, 76, 9, C_SERIGRAPHIE)                     # HD : disque
    c.thick_line(4, HEIGHT - 22, 20, HEIGHT - 6, C_SERIGRAPHIE, 3)   # BG : \
    c.thick_line(WIDTH - 20, HEIGHT - 6, WIDTH - 4, HEIGHT - 22,
                 C_SERIGRAPHIE, 3)                               # BD : /

    # Liseré de 1 px sur les 4 bords : si l'un manque à l'écran, l'image est
    # décalée ou tronquée. C'est la preuve d'AC3 sur les bords, dans l'asset.
    c.fill_rect(0, 0, WIDTH, 1, C_PISTE_VIVE)
    c.fill_rect(0, HEIGHT - 1, WIDTH, 1, C_PISTE_VIVE)
    c.fill_rect(0, 0, 1, HEIGHT, C_PISTE_VIVE)
    c.fill_rect(WIDTH - 1, 0, 1, HEIGHT, C_PISTE_VIVE)

    return c


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out-bin', help="chemin du RGB565 brut à écrire")
    ap.add_argument('--out-png', help="chemin de la prévisualisation PNG")
    ap.add_argument('--byte-order', choices=('le', 'be'), default='le',
                    help="ordre d'octets du RGB565 (défaut: le — PROUVÉ par la "
                         "mire de couleurs de dn1-2)")
    ap.add_argument('--seed', type=int, default=20260814,
                    help="graine du tirage procédural ; à graine égale, "
                         "l'asset est identique au bit près")
    args = ap.parse_args(argv)

    if not args.out_bin and not args.out_png:
        ap.error("rien à produire : donner --out-bin et/ou --out-png")

    canvas = build(args.seed)

    if args.out_bin:
        data = canvas.to_rgb565(args.byte_order)
        assert len(data) == WIDTH * HEIGHT * 2, len(data)
        d = os.path.dirname(os.path.abspath(args.out_bin))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.out_bin, 'wb') as f:
            f.write(data)
        sys.stderr.write("asset RGB565 (%s) : %s — %d octets\n"
                         % (args.byte_order, args.out_bin, len(data)))

    if args.out_png:
        png = canvas.to_png()
        d = os.path.dirname(os.path.abspath(args.out_png))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.out_png, 'wb') as f:
            f.write(png)
        sys.stderr.write("prévisualisation PNG : %s — %d octets\n"
                         % (args.out_png, len(png)))

    return 0


if __name__ == '__main__':
    sys.exit(main())
