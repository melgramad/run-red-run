# ui.py
import pygame

_TITLE_FONT = None
_BTN_FONT = None
_HUD_FONT = None

def _ensure_fonts():
    global _TITLE_FONT, _BTN_FONT, _HUD_FONT
    if _TITLE_FONT is None:
        _TITLE_FONT = pygame.font.SysFont("comic sans ms", 64)  # cute title
    if _BTN_FONT is None:
        _BTN_FONT   = pygame.font.SysFont("comic sans ms", 36)  # match style
    if _HUD_FONT is None:
        # a playful yet readable HUD font, a bit bigger
        _HUD_FONT   = pygame.font.SysFont("comic sans ms", 20, bold=True)


def draw_button(surf, rect, text, mouse_pos):
    _ensure_fonts()
    hovered = rect.collidepoint(mouse_pos)
    base   = (60, 60, 60) if not hovered else (90, 90, 90)
    border = (180, 180, 180)
    pygame.draw.rect(surf, base, rect, border_radius=12)
    pygame.draw.rect(surf, border, rect, width=2, border_radius=12)
    label = _BTN_FONT.render(text, True, (230, 230, 230))
    surf.blit(label, label.get_rect(center=rect.center))
    return hovered

def render_title(text="Run Red, Run!"):
    _ensure_fonts()
    return _TITLE_FONT.render(text, True, (230, 230, 230))

def draw_timer(surf, text, topright):
    _ensure_fonts()
    crimson = (220, 20, 60)  # crimson red like menu background
    label = _HUD_FONT.render(text, True, crimson)
    r = label.get_rect()
    r.topright = topright
    pad = r.inflate(12, 8)
    # softer backing so crimson pops
    pygame.draw.rect(surf, (0, 0, 0, 0), pad, border_radius=8)
    surf.blit(label, r)
