import pygame
from pathlib import Path

pygame.init()

# --- Window ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Run Red, Run!")
clock = pygame.time.Clock()
FPS = 60

# --- Game physics ---
GRAVITY = 0.75       # px/frame^2
JUMP_POWER = 11      # initial jump velocity (px/frame)

# Put their feet on the vertical middle of the screen
BASELINE_Y = SCREEN_HEIGHT // 2

# Little nudges to visually align feet if sprites are cropped differently
PLAYER_FOOT_OFFSET = 40  # + moves Red DOWN a bit
WOLF_FOOT_OFFSET   = 0   # + moves Wolf DOWN a bit

# --- Paths ---
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# --- Helpers ---
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

# --- Art ---
PLAYER_IDLE  = load_frames([ASSETS / "standing_1.png"], scale=2.0)[0]
PLAYER_RUN   = load_numbered("red_run_", 1, 23, scale=2.0)

WOLF_IDLE    = load_frames([ASSETS / "wolf_stand_1.png"], scale=1.5)[0]
WOLF_RUN     = load_numbered("wolf_run_", 1, 9,  scale=1.5)

# --- Entities ---
class Player(pygame.sprite.Sprite):
    def __init__(self, idle_img, run_frames, x, baseline_y, foot_offset=0, speed=5, anim_fps=12):
        super().__init__()
        self.idle_img = idle_img
        self.run_frames = run_frames
        self.frame_index = 0
        self.image = self.idle_img
        self.rect = self.image.get_rect()

        # Baseline for feet and starting position
        self.baseline_y = baseline_y + foot_offset
        self.x = x * 1.0                    # keep float for smoothness
        self.y = float(self.baseline_y)     # y = current feet position
        self.rect.midbottom = (int(self.x), int(self.y))

        # Movement/animation
        self.flip = False
        self.speed = speed
        self.frame_time_ms = 1000 // max(1, anim_fps)
        self._last_update = pygame.time.get_ticks()

        # Jump state
        self.vel_y = 0.0
        self.airborne = False

    def try_jump(self):
        # jump only if on ground
        if not self.airborne:
            self.vel_y = -JUMP_POWER
            self.airborne = True

    def move_and_animate(self, dx):
        # Horizontal move
        self.x += dx
        if dx != 0:
            self.flip = dx < 0

        # Gravity + vertical move
        self.vel_y += GRAVITY
        self.y += self.vel_y

        # Ground collision
        if self.y >= self.baseline_y:
            self.y = self.baseline_y
            self.vel_y = 0
            self.airborne = False

        # Choose frame (animate while moving horizontally OR in air; idle only when totally still on ground)
        now = pygame.time.get_ticks()
        moving_horiz = dx != 0
        if moving_horiz or self.airborne:
            if now - self._last_update >= self.frame_time_ms:
                self._last_update = now
                self.frame_index = (self.frame_index + 1) % len(self.run_frames)
            new_img = self.run_frames[self.frame_index]
        else:
            new_img = self.idle_img
            self.frame_index = 0

        # Apply new image and keep feet anchored correctly
        self.image = new_img
        self.rect = self.image.get_rect()
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

        left = self.rect.left
        self.image = new_img
        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.bottom = self.baseline_y

    def draw(self, surf):
        surf.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

# Create Red & Wolf
player = Player(PLAYER_IDLE, PLAYER_RUN, x=320, baseline_y=BASELINE_Y,
                foot_offset=PLAYER_FOOT_OFFSET, speed=5, anim_fps=12)

WOLF_EDGE_X = 8
wolf = WolfStatic(WOLF_RUN, WOLF_IDLE, left_x=WOLF_EDGE_X, baseline_y=BASELINE_Y,
                  foot_offset=WOLF_FOOT_OFFSET, anim_fps=12, flip=False)

# Start gap
STARTING_GAP = 220
player.rect.left = max(wolf.rect.right + STARTING_GAP, player.rect.left)
player.x = player.rect.midbottom[0]  # sync x with rect after manual placement

moving_left = moving_right = False
game_over = False

# --- Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: pygame.quit(); raise SystemExit
            if not game_over:
                if event.key == pygame.K_a: moving_left = True
                elif event.key == pygame.K_d: moving_right = True
                elif event.key in (pygame.K_w, pygame.K_SPACE):  # jump with W or Space
                    player.try_jump()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a: moving_left = False
            elif event.key == pygame.K_d: moving_right = False

    if not game_over:
        # horizontal velocity
        p_dx = (-player.speed if moving_left and not moving_right
                else player.speed if moving_right and not moving_left
                else 0)

        # Wolf runs only while Red moves horizontally
        wolf.set_running(p_dx != 0)
        wolf.update()

        # collision: no horizontal overlap with wolf
        next_left = player.rect.left + p_dx
        contact_line = wolf.rect.right
        if next_left <= contact_line:
            game_over = True
            player.rect.left = contact_line
            player.x = player.rect.midbottom[0]  # sync x
            player.move_and_animate(0)
        else:
            player.move_and_animate(p_dx)

        # keep Red in screen (right side)
        player.rect.right = clamp(player.rect.right, 0, SCREEN_WIDTH)
        player.x = player.rect.midbottom[0]  # keep x in sync after clamp

    screen.fill((30, 30, 30))
    wolf.draw(screen)
    player.draw(screen)

    if game_over:
        font = pygame.font.SysFont(None, 72)
        txt = font.render("GAME OVER", True, (200, 40, 40))
        screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3)))

    pygame.display.flip()
    clock.tick(FPS)













