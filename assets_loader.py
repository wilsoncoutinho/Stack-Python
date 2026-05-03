"""
Stack Attack Reborn — Asset Loading (Sprites, Fonts, Images)

Handles all image loading, sprite sheet slicing, and the HybridFont system.
Provides ready-to-use surfaces and font objects for the rest of the game.
"""
import os
import pygame
from constants import (
    ASSETS, MAGENTA, TILE_SIZE, WIDTH, HEIGHT, HUD_H,
    CRANE_FW, CHAR_DEFS, NUM_CRATE_TYPES, BOMB_TYPE, POWERUP_HELMET_TYPE,
    CRANE_FRAME_FOR_CRATE,
)

# ---------------------------------------------------------------------------
# Characters that the custom font supports (verified visually)
# ---------------------------------------------------------------------------
_CUSTOM_FONT_CHARS = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.$"
)


def _get_fallback_font(size):
    """Get a system font as fallback for special characters."""
    for name in ["Impact", "Arial Black", "Segoe UI", "Verdana"]:
        try:
            f = pygame.font.SysFont(name, size, bold=True)
            if f:
                return f
        except Exception:
            continue
    return pygame.font.SysFont(None, size)


# ---------------------------------------------------------------------------
# HybridFont — renders per-character with the correct font
# ---------------------------------------------------------------------------
class HybridFont:
    """Renders text using a custom font for supported glyphs and a system
    fallback font for special characters that would otherwise be tofu."""

    def __init__(self, custom_font, fallback_font, size):
        self.custom = custom_font
        self.fallback = fallback_font
        self._size = size
        self._char_cache = {}

    def _font_for_char(self, ch):
        if ch in _CUSTOM_FONT_CHARS or ch == ' ':
            return self.custom
        return self.fallback

    def render(self, text, antialias, color, background=None):
        # Fast path
        if all(c in _CUSTOM_FONT_CHARS or c == ' ' for c in text):
            if background:
                return self.custom.render(text, antialias, color, background)
            return self.custom.render(text, antialias, color)

        # Slow path: composite character by character
        char_surfs = []
        total_w = 0
        max_h = 0
        for ch in text:
            font = self._font_for_char(ch)
            if background:
                s = font.render(ch, antialias, color, background)
            else:
                s = font.render(ch, antialias, color)
            char_surfs.append(s)
            total_w += s.get_width()
            max_h = max(max_h, s.get_height())

        if background:
            result = pygame.Surface((total_w, max_h))
            result.fill(background)
        else:
            result = pygame.Surface((total_w, max_h), pygame.SRCALPHA)

        x = 0
        for s in char_surfs:
            y_off = max_h - s.get_height()
            result.blit(s, (x, y_off))
            x += s.get_width()
        return result

    def size(self, text):
        if all(c in _CUSTOM_FONT_CHARS or c == ' ' for c in text):
            return self.custom.size(text)
        w = 0
        h = 0
        for ch in text:
            font = self._font_for_char(ch)
            cw, ch2 = font.size(ch)
            w += cw
            h = max(h, ch2)
        return (w, h)

    def metrics(self, text):
        result = []
        for ch in text:
            font = self._font_for_char(ch)
            m = font.metrics(ch)
            result.extend(m if m else [None])
        return result

    def get_height(self):
        return self.custom.get_height()

    def get_linesize(self):
        return self.custom.get_linesize()

    def get_ascent(self):
        return self.custom.get_ascent()

    def get_descent(self):
        return self.custom.get_descent()


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------
def get_best_font(size, bold=True):
    custom_path = os.path.join(ASSETS, "jetpack-joyride-revived.ttf", "jetpack-joyride-revived.ttf")
    if os.path.exists(custom_path):
        try:
            custom = pygame.font.Font(custom_path, size)
            fallback = _get_fallback_font(size)
            return HybridFont(custom, fallback, size)
        except Exception:
            pass
    preferred = [
        "Jetpack Joyride Revived", "Jetpack Joyride", "Impact",
        "Arial Black", "Segoe UI", "Inter", "Rubik", "Outfit", "Verdana",
    ]
    for f in preferred:
        try:
            return pygame.font.SysFont(f, size, bold=bold)
        except Exception:
            continue
    return pygame.font.SysFont(None, size)


# Pre-built font instances
font_big = get_best_font(20)
font_med = get_best_font(16)
font_sm = get_best_font(10)
font_xs = get_best_font(8)


# ---------------------------------------------------------------------------
# Styled text renderer (outline + gradient)
# ---------------------------------------------------------------------------
def render_styled_text(text, font, color, outline_color=(0, 0, 0), outline_width=2, gradient=None):
    """Renders text with a thick outline and optional top-down gradient."""
    base = font.render(text, True, color)
    w, h = base.get_size()
    surf = pygame.Surface((w + outline_width * 2, h + outline_width * 2), pygame.SRCALPHA)

    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy <= outline_width * outline_width:
                out = font.render(text, True, outline_color)
                surf.blit(out, (outline_width + dx, outline_width + dy))

    shadow = font.render(text, True, (20, 20, 30))
    surf.blit(shadow, (outline_width + 2, outline_width + 2))

    if gradient:
        grad_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        c1, c2 = gradient
        for y in range(h):
            r = c1[0] + (c2[0] - c1[0]) * y / h
            g = c1[1] + (c2[1] - c1[1]) * y / h
            b = c1[2] + (c2[2] - c1[2]) * y / h
            pygame.draw.line(grad_surf, (int(r), int(g), int(b), 255), (0, y), (w, y))
        mask = font.render(text, True, (255, 255, 255))
        grad_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(grad_surf, (outline_width, outline_width))
    else:
        surf.blit(base, (outline_width, outline_width))
    return surf


# ---------------------------------------------------------------------------
# Image loading helpers
# ---------------------------------------------------------------------------
def load_img(rel_path, colorkey=MAGENTA):
    path = os.path.join(ASSETS, rel_path)
    img = pygame.image.load(path).convert()
    img.set_colorkey(colorkey)
    return img


def slice_sheet(sheet, fw, fh, scale=1.0, count=None):
    frames = []
    limit = count if count else (sheet.get_width() // fw)
    for i in range(limit):
        sub = sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh))
        w = max(1, int(fw * scale))
        h = max(1, int(fh * scale))
        frames.append(pygame.transform.scale(sub, (w, h)))
    return frames


# ---------------------------------------------------------------------------
# Load all game sprites at import time
# ---------------------------------------------------------------------------
bg_img = pygame.transform.scale(load_img("extracted/back.png"), (WIDTH, HEIGHT))
title_img = pygame.transform.scale(load_img("extracted/title.png"), (WIDTH, HEIGHT + HUD_H))

crate_sprites = slice_sheet(load_img("extracted/crates.png"), 8, 8, TILE_SIZE / 8, count=14)

try:
    bomb_sprite = pygame.image.load(os.path.join(ASSETS, "extracted/crate_bomb.png")).convert_alpha()
except Exception:
    bomb_sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
    bomb_sprite.fill((30, 30, 30))
    pygame.draw.rect(bomb_sprite, (0, 0, 0), (0, 0, TILE_SIZE, TILE_SIZE), 3)
    pygame.draw.rect(bomb_sprite, (220, 40, 40), (10, 10, 20, 20))

crane_sprites = slice_sheet(load_img("extracted/crane.png"), CRANE_FW, 18, TILE_SIZE / 8)
CRANE_SPRITE_W = crane_sprites[0].get_width() if crane_sprites else TILE_SIZE * 2
CRANE_SPRITE_H = crane_sprites[0].get_height() if crane_sprites else TILE_SIZE * 2

char_sprites = {}
char_icons = {}
for cdef in CHAR_DEFS:
    sheet = load_img("StackAttack2/" + cdef["sprite"])
    frames = slice_sheet(sheet, 8, 16, TILE_SIZE / 8)
    char_sprites[cdef["id"]] = frames
    icon_raw = load_img("StackAttack2/" + cdef["icon"])
    char_icons[cdef["id"]] = pygame.transform.scale(icon_raw, (TILE_SIZE, TILE_SIZE * 2))


# ---------------------------------------------------------------------------
# Sprite lookup helper
# ---------------------------------------------------------------------------
def crate_sprite_for_type(crate_type):
    if crate_type == BOMB_TYPE:
        return bomb_sprite
    if crate_type == POWERUP_HELMET_TYPE:
        return crate_sprites[5]
    return crate_sprites[(crate_type - 1) % NUM_CRATE_TYPES]
