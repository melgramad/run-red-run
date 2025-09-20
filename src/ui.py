# ui.py
import pygame

_TITLE_FONT = None
_BTN_FONT = None

def _ensure_fonts():
    global _TITLE_FONT, _BTN_FONT
    if _TITLE_FONT is None:
        _TITLE_FONT = pygame.font.SysFont(None, 64)
        _BTN_FONT   = pygame.font.SysFont(None, 36)

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


