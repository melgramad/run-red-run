# run_red_run.py — single-file build of "Run, Red, Run!"
# Requires: Python 3.10+, pygame
# Assets expected in: ./assets/
#   red_idle_1.png ... red_idle_8.png
#   red_run_1.png  ... red_run_23.png
#   wolf_stand_1.png
#   wolf_run_1.png ... wolf_run_9.png
#   Video-Project.ogg (menu music, optional)
#   game_loop.ogg     (game music, optional)

import sys
import pygame
from pathlib import Path

# ----------------------------
# SETTINGS (formerly settings.py)
# ----------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
FPS = 60

# Colors
GAME_BG = (30, 30, 30)
MENU_BG = (85, 22, 22)  # deep, nearly-black crimson

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_ROOT  = PROJECT_ROOT.parent / "assets"

# Physics & layout
GRAVITY = 0.45
JUMP_POWER = 11
BASELINE_Y = SCREEN_HEIGHT // 2
PLAYER_FOOT_OFFSET = 50
WOLF_FOOT_OFFSET = 0
WOLF_EDGE_X = 8
STARTING_GAP = 220

# Audio
MENU_VOLUME = 0.6
GAME_VOLUME = 0.6

# ----------------------------
# ASSET LOADER (formerly asset_loader.py)
# ----------------------------
def _placeholder_surface(w=64, h=64, text="missing"):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((90, 30, 30))
    pygame.draw.rect(surf, (200, 60, 60), surf.get_rect(), 3)
    try:
        f = pygame.font.SysFont(None, 16)
        lbl = f.render(text, True, (230, 230, 230))
        r = lbl.get_rect(center=surf.get_rect().center)
        surf.blit(lbl, r)
    except Exception:
        pass
    return surf

def load_frames(paths, scale=1.0):
    frames = []
    for p in paths:
        try:
            img = pygame.image.load(str(p)).convert_alpha()
            if scale != 1.0:
                img = pygame.transform.scale(
                    img, (int(img.get_width() * scale), int(img.get_height() * scale))
                )
            frames.append(img)
        except Exception:
            # soft-fail: add a placeholder so the game can still run
            frames.append(_placeholder_surface(int(32*scale), int(32*scale), "asset"))
    return frames

def load_numbered(prefix, start, end, ext=".png", scale=1.0):
    files = []
    for i in range(start, end + 1):
        fp = ASSETS_ROOT / f"{prefix}{i}{ext}"
        if fp.is_file():
            files.append(fp)
    if not files:
        # no frames found; return one placeholder
        return [ _placeholder_surface(int(32*scale), int(32*scale), f"{prefix}*") ]
    return load_frames(files, scale)

# ----------------------------
# AUDIO (formerly audio.py)
# ----------------------------
MENU_MUSIC = ASSETS_ROOT / "Video-Project.ogg"
GAME_MUSIC = ASSETS_ROOT / "game_loop.ogg"

def init_audio():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except Exception:
        # If sound device isn't available, keep going silently.
        pass

def play_menu_music(start_at=3.0):
    try:
        if MENU_MUSIC.is_file():
            pygame.mixer.music.load(str(MENU_MUSIC))
            pygame.mixer.music.set_volume(MENU_VOLUME)
            pygame.mixer.music.play(-1, start_at)
    except Exception:
        pass

def play_game_music(start_at=3.0):
    try:
        if GAME_MUSIC.is_file():
            pygame.mixer.music.load(str(GAME_MUSIC))
            pygame.mixer.music.set_volume(GAME_VOLUME)
            pygame.mixer.music.play(-1, start_at, fade_ms=600)
        else:
            pygame.mixer.music.fadeout(500)
    except Exception:
        pass

def fade_out(ms=500):
    try:
        pygame.mixer.music.fadeout(ms)
    except Exception:
        pass

# ----------------------------
# UI (formerly ui.py)
# ----------------------------
_TITLE_FONT = None
_BTN_FONT = None
_HUD_FONT = None

def _ensure_fonts():
    global _TITLE_FONT, _BTN_FONT, _HUD_FONT
    if _TITLE_FONT is None:
        _TITLE_FONT = pygame.font.SysFont("comic sans ms", 64)
    if _BTN_FONT is None:
        _BTN_FONT   = pygame.font.SysFont("comic sans ms", 36)
    if _HUD_FONT is None:
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
    crimson = (220, 20, 60)
    label = _HUD_FONT.render(text, True, crimson)
    r = label.get_rect()
    r.topright = topright
    pad = r.inflate(12, 8)
    pygame.draw.rect(surf, (0, 0, 0, 0), pad, border_radius=8)
    surf.blit(label, r)

# ----------------------------
# ENTITIES (formerly entities.py)
# ----------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, idle_frames, run_frames, x, baseline_y,
                 foot_offset=0, speed=5, anim_fps=12):
        super().__init__()
        self.idle_frames = idle_frames or []
        self.run_frames  = run_frames or []
        self.frame_index = 0

        first_img = (self.idle_frames[0] if self.idle_frames
                     else self.run_frames[0] if self.run_frames
                     else pygame.Surface((1, 1), pygame.SRCALPHA))

        self.image = first_img
        self.rect  = self.image.get_rect()

        self.baseline_y = baseline_y + foot_offset
        self.x = float(x)
        self.y = float(self.baseline_y)
        self.rect.midbottom = (int(self.x), int(self.y))

        self.flip = False
        self.speed = speed
        self.frame_time_ms = 1000 // max(1, anim_fps)
        self._last_update = pygame.time.get_ticks()

        self.vel_y = 0.0
        self.airborne = False
        self.jump_power = JUMP_POWER

    def try_jump(self):
        if not self.airborne:
            self.vel_y = -self.jump_power
            self.airborne = True

    def move_and_animate(self, dx: float):
        self.x += dx
        if dx != 0:
            self.flip = dx < 0

        self.vel_y += GRAVITY
        self.y += self.vel_y
        if self.y >= self.baseline_y:
            self.y = self.baseline_y
            self.vel_y = 0
            self.airborne = False

        seq = self.run_frames if (dx != 0 or self.airborne) else self.idle_frames
        if not seq:
            left = self.rect.left
            self.rect = self.image.get_rect()
            self.rect.left = left
            self.rect.midbottom = (int(self.x), int(self.y))
            return

        now = pygame.time.get_ticks()
        if now - self._last_update >= self.frame_time_ms:
            self._last_update = now
            self.frame_index = (self.frame_index + 1) % len(seq)
        else:
            self.frame_index %= len(seq)

        self.image = seq[self.frame_index]
        left = self.rect.left
        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.midbottom = (int(self.x), int(self.y))

    def draw(self, surf: pygame.Surface):
        surf.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class WolfStatic(pygame.sprite.Sprite):
    def __init__(self, run_frames, idle_img, left_x, baseline_y,
                 foot_offset=0, anim_fps=12, flip=False):
        super().__init__()
        self.frames = run_frames or []
        self.idle_img = idle_img
        self.frame_index = 0

        self.image = self.idle_img if self.idle_img is not None else (
            self.frames[0] if self.frames else pygame.Surface((1, 1), pygame.SRCALPHA)
        )
        self.rect = self.image.get_rect()

        self.flip = flip
        self.baseline_y = baseline_y + foot_offset
        self.left_x = left_x
        self.frame_time_ms = 1000 // max(1, anim_fps)
        self._last_update = pygame.time.get_ticks()
        self.running = False

        self.rect.left = self.left_x
        self.rect.bottom = self.baseline_y

    def set_running(self, running: bool):
        self.running = running

    def update(self):
        if not self.running or not self.frames:
            new_img = self.idle_img
            self.frame_index = 0
        else:
            now = pygame.time.get_ticks()
            if now - self._last_update >= self.frame_time_ms:
                self._last_update = now
                self.frame_index = (self.frame_index + 1) % len(self.frames)
            else:
                self.frame_index %= len(self.frames)
            new_img = self.frames[self.frame_index]

        left = self.rect.left
        bottom = self.baseline_y
        self.image = new_img if new_img is not None else self.image
        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.bottom = bottom

    def draw(self, surf: pygame.Surface):
        surf.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class IdleBreather:
    def __init__(self, frames, x, baseline_y, anim_fps=10):
        self.frames = frames or []
        self.index = 0
        self.image = self.frames[0] if self.frames else pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect  = self.image.get_rect()
        self.rect.midbottom = (x, baseline_y)
        self.baseline_y = baseline_y
        self.frame_time_ms = 1000 // max(1, anim_fps)
        self._last = pygame.time.get_ticks()

    def update(self):
        if not self.frames:
            return
        now = pygame.time.get_ticks()
        if now - self._last >= self.frame_time_ms:
            self._last = now
            self.index = (self.index + 1) % len(self.frames)
            left = self.rect.left
            self.image = self.frames[self.index]
            self.rect  = self.image.get_rect()
            self.rect.left = left
            self.rect.bottom = self.baseline_y

    def draw(self, surf: pygame.Surface):
        surf.blit(self.image, self.rect)

# ----------------------------
# FRAME NORMALIZER (from your main)
# ----------------------------
def normalize_frames(frames, anchor="midbottom"):
    if not frames:
        return frames
    max_w = max(f.get_width()  for f in frames)
    max_h = max(f.get_height() for f in frames)
    norm = []
    for f in frames:
        r = f.get_rect()
        if   anchor == "midbottom": an = r.midbottom
        elif anchor == "midtop":    an = r.midtop
        elif anchor == "midleft":   an = r.midleft
        elif anchor == "midright":  an = r.midright
        elif anchor == "center":    an = r.center
        else:                       an = r.midbottom
        canvas = pygame.Surface((max_w, max_h), pygame.SRCALPHA, 32).convert_alpha()
        dst_r = canvas.get_rect()
        if   anchor == "midbottom": dst_anchor = dst_r.midbottom
        elif anchor == "midtop":    dst_anchor = dst_r.midtop
        elif anchor == "midleft":   dst_anchor = dst_r.midleft
        elif anchor == "midright":  dst_anchor = dst_r.midright
        elif anchor == "center":    dst_anchor = dst_r.center
        else:                       dst_anchor = dst_r.midbottom
        ox = dst_anchor[0] - an[0]
        oy = dst_anchor[1] - an[1]
        canvas.blit(f, (ox, oy))
        norm.append(canvas)
    return norm

# ----------------------------
# MAIN
# ----------------------------
def main():
    pygame.init()  # init BEFORE anything that uses fonts/audio
    init_audio()

    # ---------- WINDOW ----------
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Run, Red, Run!")
    clock = pygame.time.Clock()

    # ---------- ART ----------
    PLAYER_IDLE_FRAMES = load_numbered("red_idle_", 1 , 8,  scale=2.0)
    PLAYER_RUN         = load_numbered("red_run_",  1, 23, scale=2.0)

    wolf_idle_list     = load_frames([ASSETS_ROOT / "wolf_stand_1.png"], scale=1.5)
    WOLF_IDLE          = wolf_idle_list[0] if wolf_idle_list else _placeholder_surface(64, 64, "wolf_idle")
    WOLF_RUN           = load_numbered("wolf_run_", 1, 9, scale=1.5)

    PLAYER_IDLE_FRAMES = normalize_frames(PLAYER_IDLE_FRAMES, anchor="midbottom")
    PLAYER_RUN         = normalize_frames(PLAYER_RUN,         anchor="midbottom")

    # ---------- ENTITIES ----------
    player = Player(
        PLAYER_IDLE_FRAMES, PLAYER_RUN,
        x=320, baseline_y=BASELINE_Y,
        foot_offset=PLAYER_FOOT_OFFSET,
        speed=5, anim_fps=10
    )
    wolf = WolfStatic(
        WOLF_RUN, WOLF_IDLE,
        left_x=WOLF_EDGE_X,
        baseline_y=BASELINE_Y,
        foot_offset=WOLF_FOOT_OFFSET,
        anim_fps=12, flip=False
    )

    # Separate them at start
    player.rect.left = max(wolf.rect.right + STARTING_GAP, player.rect.left)
    player.x = player.rect.midbottom[0]

    # ---------- MENU SETUP ----------
    state = "menu"
    play_menu_music()

    title_surf = render_title("Run Red, Run!")
    btn_w, btn_h = 240, 56
    start_rect = pygame.Rect(0, 0, btn_w, btn_h)
    exit_rect  = pygame.Rect(0, 0, btn_w, btn_h)
    start_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
    exit_rect.center  = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 80)

    menu_red = IdleBreather(
        PLAYER_IDLE_FRAMES,
        x=SCREEN_WIDTH // 2,
        baseline_y=exit_rect.bottom + 140,
        anim_fps=10
    )

    moving_left = moving_right = False
    game_over = False

    # ---------- TIMER ----------
    timer_start_ms = None
    elapsed_ms = 0

    # ---------- MAIN LOOP ----------
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_rect.collidepoint(event.pos):
                        state = "game"
                        play_game_music()
                        timer_start_ms = pygame.time.get_ticks()
                        elapsed_ms = 0
                    elif exit_rect.collidepoint(event.pos):
                        running = False
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if not game_over:
                        if event.key == pygame.K_a: moving_left = True
                        elif event.key == pygame.K_d: moving_right = True
                        elif event.key in (pygame.K_w, pygame.K_SPACE):
                            player.try_jump()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_a: moving_left = False
                    elif event.key == pygame.K_d: moving_right = False

        if state == "menu":
            screen.fill(MENU_BG)
            screen.blit(title_surf, title_surf.get_rect(
                center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//6)))
            mouse_pos = pygame.mouse.get_pos()
            draw_button(screen, start_rect, "Start", mouse_pos)
            draw_button(screen, exit_rect,  "Exit",  mouse_pos)
            menu_red.update(); menu_red.draw(screen)

        else:
            screen.fill(GAME_BG)

            if not game_over:
                if timer_start_ms is not None:
                    now = pygame.time.get_ticks()
                    elapsed_ms = now - timer_start_ms

                p_dx = (-player.speed if moving_left and not moving_right
                        else player.speed if moving_right and not moving_left
                        else 0)

                wolf.set_running(p_dx != 0)
                wolf.update()

                next_left = player.rect.left + p_dx
                contact_line = wolf.rect.right
                if next_left <= contact_line:
                    game_over = True
                    player.rect.left = contact_line
                    player.x = player.rect.midbottom[0]
                    player.move_and_animate(0)
                else:
                    player.move_and_animate(p_dx)

                # keep on screen horizontally
                player.rect.right = max(0, min(player.rect.right, SCREEN_WIDTH))
                player.x = player.rect.midbottom[0]

            wolf.draw(screen)
            player.draw(screen)

            total_sec = elapsed_ms // 1000
            mm = total_sec // 60; ss = total_sec % 60
            tenths = (elapsed_ms % 1000) // 100
            timer_text = f"{mm:02d}:{ss:02d}.{tenths}"
            draw_timer(screen, timer_text, (SCREEN_WIDTH - 12, 12))

            if game_over:
                font = pygame.font.SysFont(None, 72)
                txt = font.render("GAME OVER", True, (200, 40, 40))
                screen.blit(txt, txt.get_rect(
                    center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)

# ----------------------------
# ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    main()








