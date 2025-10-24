import sys, pygame, json
from pathlib import Path

# ----------------------------
# SETTINGS
# ----------------------------
SCREEN_WIDTH  = 1100
SCREEN_HEIGHT = 740
LOWER_MARGIN  = 100
SIDE_MARGIN   = 300
FPS           = 60
ROWS          = 16
TILE_SIZE     = SCREEN_HEIGHT // ROWS

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_ROOT  = PROJECT_ROOT / "assets"
ASSETS       = PROJECT_ROOT / "assets" / "LevelEditor-main" / "LevelEditor-main" / "img"
TILE_ASSETS  = ASSETS / "tile"
OBJ_ASSETS   = TILE_ASSETS / "Objects_Animated"
BG_ASSETS    = ASSETS / "Background"
LEVEL_FILE   = PROJECT_ROOT / "src" / "level.json"

# Colors
WHITE  = (255, 255, 255)
GAME_BG = (30, 30, 30)

# ----------------------------
# INIT
# ----------------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN), pygame.RESIZABLE)
pygame.display.set_caption("Run Red, Run!")
clock = pygame.time.Clock()

# ----------------------------
# LOAD BACKGROUND
# ----------------------------
def load_image_safe(path):
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except Exception:
        surf = pygame.Surface((64, 64)); surf.fill((255, 0, 255)); return surf

sky_img      = load_image_safe(BG_ASSETS / "sky_cloud.png")
mountain_img = load_image_safe(BG_ASSETS / "mountain.png")
pine1_img    = load_image_safe(BG_ASSETS / "pine1.png")
pine2_img    = load_image_safe(BG_ASSETS / "pine2.png")

# ----------------------------
# LOAD TILES + STAR
# ----------------------------
img_list = [load_image_safe(p) for p in sorted(TILE_ASSETS.glob("*.png"))]
if not img_list:
    raise FileNotFoundError(f"No tile images found in {TILE_ASSETS}")

STAR_IMG = load_image_safe(OBJ_ASSETS / "Star.png")

# ----------------------------
# LOAD PLAYER FRAMES (Red)
# ----------------------------
def load_frames(prefix, start, end, scale=1.0):
    frames = []
    for i in range(start, end + 1):
        fp = ASSETS_ROOT / f"{prefix}{i}.png"
        if fp.exists():
            img = load_image_safe(fp)
            if scale != 1.0:
                img = pygame.transform.scale(img, (int(img.get_width()*scale), int(img.get_height()*scale)))
            frames.append(img)
    if not frames:
        surf = pygame.Surface((64, 64)); surf.fill((255, 0, 255)); frames.append(surf)
    return frames

PLAYER_SCALE = 2.0
PLAYER_IDLE_FRAMES = load_frames("red_idle_", 1, 8,  PLAYER_SCALE)
PLAYER_RUN         = load_frames("red_run_",  1, 23, PLAYER_SCALE)

# ----------------------------
# WORLD
# ----------------------------
class World:
    def __init__(self):
        self.tile_list = []
        self.obstacle_list = []
        self.kill_list = []
        self.star_list = []

    def process_data(self, data):
        self.tile_list.clear(); self.obstacle_list.clear(); self.kill_list.clear(); self.star_list.clear()
        for entry in data:
            tile_index = entry.get("tile_index", -1)
            gx = entry.get("x", 0)
            gy = entry.get("y", 0)
            scale = max(0.1, entry.get("scale", 1.0))
            px, py = int(gx * TILE_SIZE), int(gy * TILE_SIZE)
            if 0 <= tile_index < len(img_list):
                img = pygame.transform.scale(img_list[tile_index], (int(TILE_SIZE * scale), int(TILE_SIZE * scale)))
                rect = pygame.Rect(px, py, img.get_width(), img.get_height())
                self.tile_list.append((img, rect))
                if tile_index == 14:
                    self.kill_list.append((img, rect))
                if tile_index in (5, 3) or (129 <= tile_index <= 133) or (58 <= tile_index <= 93):
                    self.obstacle_list.append((img, rect))

            # detect star placement
            if "star" in str(entry.get("texture_path", "")).lower():
                rect = pygame.Rect(px, py, STAR_IMG.get_width(), STAR_IMG.get_height())
                self.star_list.append((STAR_IMG, rect))

    def draw(self, surf, scroll):
        for img, rect in self.tile_list:
            surf.blit(img, (rect.x - scroll, rect.y))
        for img, rect in self.star_list:
            surf.blit(img, (rect.x - scroll, rect.y))

# ----------------------------
# PLAYER (Red)
# ----------------------------
GRAVITY = 0.85
JUMP_POWER = 12
BASELINE_Y = SCREEN_HEIGHT - 90
PLAYER_FOOT_OFFSET = 0

class Player(pygame.sprite.Sprite):
    def __init__(self, idle_frames, run_frames, x, baseline_y, foot_offset=0, speed=6):
        super().__init__()
        self.idle_frames = idle_frames or []
        self.run_frames  = run_frames or []
        self._seq = self.idle_frames if self.idle_frames else self.run_frames
        self.frame_index = 0
        self.image = (self._seq[0] if self._seq else pygame.Surface((64,64)))
        self.rect  = self.image.get_rect()
        self.baseline_y = baseline_y + foot_offset
        self.x = float(x)
        self.y = float(self.baseline_y)
        self.rect.midbottom = (int(self.x), int(self.y))
        self.flip = False
        self.base_speed = speed
        self.speed = speed
        self.vel_y = 0.0
        self.airborne = False
        self.boost_timer = 0
        self.frame_time_ms = 1000 // 12
        self._last_update  = pygame.time.get_ticks()

    def try_jump(self):
        if not self.airborne:
            self.vel_y = -JUMP_POWER
            self.airborne = True

    def move_and_animate(self, dx, obstacles):
        # ---- Horizontal
        self.x += dx
        self.rect.midbottom = (int(self.x), int(self.y))
        for _, r in obstacles:
            if self.rect.colliderect(r):
                if dx > 0:
                    if self.rect.bottom - r.top < TILE_SIZE * 0.4:
                        self.rect.bottom = r.top; self.vel_y = 0; self.airborne = False
                    else:
                        self.rect.right = r.left
                elif dx < 0:
                    if self.rect.bottom - r.top < TILE_SIZE * 0.4:
                        self.rect.bottom = r.top; self.vel_y = 0; self.airborne = False
                    else:
                        self.rect.left = r.right
                self.x = self.rect.midbottom[0]

        # ---- Vertical
        self.vel_y += GRAVITY
        self.y += self.vel_y
        self.rect.midbottom = (int(self.x), int(self.y))
        for _, r in obstacles:
            if self.rect.colliderect(r):
                if self.vel_y > 0:
                    self.rect.bottom = r.top; self.vel_y = 0; self.airborne = False
                elif self.vel_y < 0:
                    self.rect.top = r.bottom; self.vel_y = 0
                self.y = self.rect.midbottom[1]

        # ---- Animation
        seq = self.run_frames if dx != 0 or self.airborne else self.idle_frames
        if seq != getattr(self, "_seq", None):
            self.frame_index = 0; self._seq = seq
        if self._seq:
            now = pygame.time.get_ticks()
            if now - self._last_update > self.frame_time_ms:
                self._last_update = now
                self.frame_index = (self.frame_index + 1) % len(self._seq)
            self.image = self._seq[self.frame_index]

        old_midbottom = self.rect.midbottom
        self.rect = self.image.get_rect()
        self.rect.midbottom = old_midbottom
        self.x = float(self.rect.midbottom[0]); self.y = float(self.rect.midbottom[1])

    def update_boost(self):
        if self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer == 0:
                self.speed = self.base_speed

    def boost(self, duration=180, multiplier=1.8):  # 180 frames ≈ 3 seconds
        self.speed = self.base_speed * multiplier
        self.boost_timer = duration

    def draw(self, surf, scroll):
        surf.blit(pygame.transform.flip(self.image, self.flip, False),
                  (self.rect.x - scroll, self.rect.y))

# ----------------------------
# AUDIO (game)
# ----------------------------
GAME_MUSIC = ASSETS_ROOT / "game_loop.ogg"
def play_game_music():
    try:
        if GAME_MUSIC.is_file():
            pygame.mixer.music.load(str(GAME_MUSIC))
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play(-1, start=0.0)
    except Exception:
        pass

# ----------------------------
# MAIN LOOP
# ----------------------------
def main():
    if LEVEL_FILE.exists():
        level_data = json.loads(Path(LEVEL_FILE).read_text())
    else:
        level_data = []

    world = World()
    world.process_data(level_data)

    player = Player(PLAYER_IDLE_FRAMES, PLAYER_RUN, 100, BASELINE_Y, PLAYER_FOOT_OFFSET, speed=6)
    scroll = 0
    moving_left = moving_right = False

    play_game_music()

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(GAME_BG)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_a: moving_left = True
                if e.key == pygame.K_d: moving_right = True
                if e.key in (pygame.K_w, pygame.K_SPACE): player.try_jump()
                if e.key == pygame.K_ESCAPE: running = False
            elif e.type == pygame.KEYUP:
                if e.key == pygame.K_a: moving_left = False
                if e.key == pygame.K_d: moving_right = False

        dx = (-player.speed if moving_left else player.speed if moving_right else 0)

        # ----- Camera scroll (never below 0)
        screen_center_x = SCREEN_WIDTH // 2
        player_screen_x = player.x - scroll
        if player_screen_x > screen_center_x and dx > 0:
            scroll += dx
        elif player_screen_x < screen_center_x and dx < 0 and scroll > 0:
            scroll += dx
        scroll = max(0, scroll)

        # ----- Prevent leaving left side
        if scroll == 0 and (player.x - scroll) < (player.rect.width / 2):
            player.x = scroll + (player.rect.width / 2)

        # ----- Parallax BG
        for i in range(16):
            off = i * sky_img.get_width()
            screen.blit(sky_img,      (off - scroll * 0.4, 0))
            screen.blit(mountain_img, (off - scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 260))
            screen.blit(pine1_img,    (off - scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 100))
            screen.blit(pine2_img,    (off - scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height() + 20))

        # ----- Draw + update
        world.draw(screen, scroll)
        player.move_and_animate(dx, world.obstacle_list)

        # ⭐ Star collision check
        for img, rect in world.star_list:
            if player.rect.colliderect(rect):
                player.boost()  # 3 sec boost
                world.star_list.remove((img, rect))  # remove star after pickup
                break

        # Lethal check (tile_index == 14)
        for _, r in world.kill_list:
            if player.rect.colliderect(r):
                player.x, player.y = 100, BASELINE_Y
                player.vel_y, player.airborne, scroll = 0, False, 0
                break

        player.update_boost()
        player.draw(screen, scroll)
        pygame.display.flip()

    pygame.quit(); sys.exit(0)

if __name__ == "__main__":
    main()
