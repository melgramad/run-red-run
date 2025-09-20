import pygame
from pathlib import Path

pygame.init()

# ---------- WINDOW ----------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Run Red, Run!")
clock = pygame.time.Clock()
FPS = 60
# ---------- COLORS ----------
GAME_BG  = (30, 30, 30)         # current gameplay background
MENU_BG  = (16, 2, 4)           # deep dark crimson (almost black)



# ---------- PHYSICS / LAYOUT ----------
GRAVITY = 0.75          # px/frame^2
JUMP_POWER = 11         # initial jump velocity (px/frame)
BASELINE_Y = SCREEN_HEIGHT // 2       # feet line for gameplay (center of screen)
PLAYER_FOOT_OFFSET = 40               # tweak if Red's feet look high/low
WOLF_FOOT_OFFSET   = 0                # tweak if Wolf's feet look high/low

# ---------- PATHS ----------
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"              # put all images here

# ---------- HELPERS ----------
def load_frames(paths, scale=3.0):
    frames = []
    for p in paths:
        img = pygame.image.load(str(p)).convert_alpha()
        img = pygame.transform.scale(
            img, (int(img.get_width()*scale), int(img.get_height()*scale))
        )
        frames.append(img)
    return frames

def load_numbered(prefix, start, end, ext=".png", scale=1.0):
    files = [ASSETS / f"{prefix}{i}{ext}" for i in range(start, end + 1)]
    return load_frames(files, scale)

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

# simple UI button
TITLE_FONT = pygame.font.SysFont(None, 64)
BTN_FONT   = pygame.font.SysFont(None, 36)
def draw_button(surf, rect, text, mouse_pos):
    hovered = rect.collidepoint(mouse_pos)
    base = (60, 60, 60) if not hovered else (90, 90, 90)
    border = (180, 180, 180)
    pygame.draw.rect(surf, base, rect, border_radius=12)
    pygame.draw.rect(surf, border, rect, width=2, border_radius=12)
    label = BTN_FONT.render(text, True, (230, 230, 230))
    surf.blit(label, label.get_rect(center=rect.center))
    return hovered

# ---------- ART ----------
# Red idle breathing sequence and run sequence
PLAYER_IDLE_FRAMES = load_numbered("red_idle_", 1, 18, scale=2.0)   # red_idle_1..18.png
PLAYER_RUN         = load_numbered("red_run_",  1, 23, scale=2.0)   # adjust end if you have fewer

# Wolf idle + run
WOLF_IDLE = load_frames([ASSETS / "wolf_stand_1.png"], scale=1.5)[0]
WOLF_RUN  = load_numbered("wolf_run_", 1, 9, scale=1.5)

# ---------- ENTITIES ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, idle_frames, run_frames, x, baseline_y, foot_offset=0, speed=5, anim_fps=12):
        super().__init__()
        self.idle_frames = idle_frames
        self.run_frames  = run_frames
        self.frame_index = 0
        self.image = self.idle_frames[0]
        self.rect  = self.image.get_rect()

        # feet baseline & position
        self.baseline_y = baseline_y + foot_offset
        self.x = float(x)
        self.y = float(self.baseline_y)
        self.rect.midbottom = (int(self.x), int(self.y))

        # movement / anim
        self.flip = False
        self.speed = speed
        self.frame_time_ms = 1000 // max(1, anim_fps)
        self._last_update = pygame.time.get_ticks()

        # jump state
        self.vel_y = 0.0
        self.airborne = False

    def try_jump(self):
        if not self.airborne:
            self.vel_y = -JUMP_POWER
            self.airborne = True

    def move_and_animate(self, dx):
        # horizontal
        self.x += dx
        if dx != 0:
            self.flip = dx < 0

        # vertical physics
        self.vel_y += GRAVITY
        self.y += self.vel_y
        if self.y >= self.baseline_y:
            self.y = self.baseline_y
            self.vel_y = 0
            self.airborne = False

        # choose sequence (run if moving or airborne, else idle breathing)
        seq = self.run_frames if (dx != 0 or self.airborne) else self.idle_frames

        # advance animation
        now = pygame.time.get_ticks()
        if now - self._last_update >= self.frame_time_ms:
            self._last_update = now
            self.frame_index = (self.frame_index + 1) % len(seq)
        new_img = seq[self.frame_index]

        # apply & keep feet pinned
        self.image = new_img
        self.rect  = self.image.get_rect()
        self.rect.midbottom = (int(self.x), int(self.y))

    def draw(self, surf):
        surf.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class WolfStatic(pygame.sprite.Sprite):
    """Wolf pinned to left edge; runs only when `running=True`, else idle."""
    def __init__(self, run_frames, idle_img, left_x, baseline_y, foot_offset=0, anim_fps=12, flip=False):
        super().__init__()
        self.frames = run_frames
        self.idle_img = idle_img
        self.frame_index = 0
        self.image = self.idle_img
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
        if not self.running:
            new_img = self.idle_img
            self.frame_index = 0
        else:
            now = pygame.time.get_ticks()
            if now - self._last_update >= self.frame_time_ms:
                self._last_update = now
                self.frame_index = (self.frame_index + 1) % len(self.frames)
            new_img = self.frames[self.frame_index]

        # swap while preserving baseline + left pin
        left = self.rect.left
        self.image = new_img
        self.rect  = self.image.get_rect()
        self.rect.left = left
        self.rect.bottom = self.baseline_y

    def draw(self, surf):
        surf.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class IdleBreather:
    """Menu widget: animates Red's idle frames on a fixed baseline."""
    def __init__(self, frames, x, baseline_y, anim_fps=10):
        self.frames = frames
        self.index = 0
        self.image = frames[0]
        self.rect  = self.image.get_rect()
        self.rect.midbottom = (x, baseline_y)
        self.baseline_y = baseline_y
        self.frame_time_ms = 1000 // max(1, anim_fps)
        self._last = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self._last >= self.frame_time_ms:
            self._last = now
            self.index = (self.index + 1) % len(self.frames)
            left = self.rect.left
            self.image = self.frames[self.index]
            self.rect  = self.image.get_rect()
            self.rect.left = left
            self.rect.bottom = self.baseline_y

    def draw(self, surf):
        surf.blit(self.image, self.rect)

# ---------- BUILD GAME ENTITIES ----------
player = Player(PLAYER_IDLE_FRAMES, PLAYER_RUN, x=320,
                baseline_y=BASELINE_Y, foot_offset=PLAYER_FOOT_OFFSET,
                speed=5, anim_fps=12)

WOLF_EDGE_X = 8
wolf = WolfStatic(WOLF_RUN, WOLF_IDLE, left_x=WOLF_EDGE_X,
                  baseline_y=BASELINE_Y, foot_offset=WOLF_FOOT_OFFSET,
                  anim_fps=12, flip=False)

# Give them a comfy starting gap
STARTING_GAP = 220
player.rect.left = max(wolf.rect.right + STARTING_GAP, player.rect.left)
player.x = player.rect.midbottom[0]  # keep x in sync after manual placement

# ---------- MENU SETUP ----------
state = "menu"  # 'menu' -> 'game'
title_surf = TITLE_FONT.render("Run Red, Run!", True, (230, 230, 230))

btn_w, btn_h = 240, 56
start_rect = pygame.Rect(0, 0, btn_w, btn_h)
exit_rect  = pygame.Rect(0, 0, btn_w, btn_h)
start_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
exit_rect.center  = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 80)

# Red's idle animation on the menu (under buttons)
menu_red = IdleBreather(PLAYER_IDLE_FRAMES,
                        x=SCREEN_WIDTH // 2,
                        baseline_y=exit_rect.bottom + 140,
                        anim_fps=10)

# ---------- INPUT FLAGS ----------
moving_left = moving_right = False
game_over = False

# ---------- MAIN LOOP ----------
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit

        if state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_rect.collidepoint(event.pos):
                    state = "game"
                elif exit_rect.collidepoint(event.pos):
                    pygame.quit(); raise SystemExit
        else:  # gameplay
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: pygame.quit(); raise SystemExit
                if not game_over:
                    if event.key == pygame.K_a: moving_left = True
                    elif event.key == pygame.K_d: moving_right = True
                    elif event.key in (pygame.K_w, pygame.K_SPACE):  # jump
                        player.try_jump()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a: moving_left = False
                elif event.key == pygame.K_d: moving_right = False

    # ---------- UPDATE & DRAW ----------
    if state == "menu":
        screen.fill(MENU_BG)
    else:
        screen.fill(GAME_BG)


    if state == "menu":
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//6)))
        mouse_pos = pygame.mouse.get_pos()
        draw_button(screen, start_rect, "Start", mouse_pos)
        draw_button(screen, exit_rect,  "Exit",  mouse_pos)

        menu_red.update()
        menu_red.draw(screen)

    else:
        if not game_over:
            # horizontal velocity from A/D
            p_dx = (-player.speed if moving_left and not moving_right
                    else player.speed if moving_right and not moving_left
                    else 0)

            # wolf runs only while Red moves horizontally
            wolf.set_running(p_dx != 0)
            wolf.update()

            # collision rule: no overlap with wolf (game over)
            next_left = player.rect.left + p_dx
            contact_line = wolf.rect.right
            if next_left <= contact_line:
                game_over = True
                player.rect.left = contact_line
                player.x = player.rect.midbottom[0]
                player.move_and_animate(0)
            else:
                player.move_and_animate(p_dx)

            # keep Red inside the right boundary
            player.rect.right = clamp(player.rect.right, 0, SCREEN_WIDTH)
            player.x = player.rect.midbottom[0]

        wolf.draw(screen)
        player.draw(screen)

        if game_over:
            font = pygame.font.SysFont(None, 72)
            txt = font.render("GAME OVER", True, (200, 40, 40))
            screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3)))

    pygame.display.flip()
    clock.tick(FPS)














