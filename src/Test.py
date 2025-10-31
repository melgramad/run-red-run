import sys
import pygame
import os
import random
from pathlib import Path
import json

# ----------------------------
# MUSIC
# ----------------------------
GAME_MUSIC = Path(r"C:\Dev\orgsOfLangs\run-red-run\assets\KingdomDance.mp3")

def play_game_music():
    try:
        if GAME_MUSIC.exists():
            pygame.mixer.music.load(str(GAME_MUSIC))
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play(-1, fade_ms=4000)
            print("Now playing:", GAME_MUSIC.name)
        else:
            print("Music not found:", GAME_MUSIC)
    except Exception as e:
        print("Audio error:", e)

# ----------------------------
# SOUND EFFECTS (.WAV)
# ----------------------------
SFX_PATHS = {
    "jump":      Path(r"C:\Dev\orgsOfLangs\run-red-run\assets\sfx\jump.wav"),
    "lose":      Path(r"C:\Dev\orgsOfLangs\run-red-run\assets\sfx\lose.wav"),
    "win":       Path(r"C:\Dev\orgsOfLangs\run-red-run\assets\sfx\win.wav"),
    "vineclimb": Path(r"C:\Dev\orgsOfLangs\run-red-run\assets\sfx\vineclimb.wav"),
    "wolfhowl":  Path(r"C:\Dev\orgsOfLangs\run-red-run\assets\sfx\wolfhowl.wav"),
}

def load_sfx(path):
    try:
        if path.exists():
            snd = pygame.mixer.Sound(str(path))
            snd.set_volume(0.9)
            return snd
        else:
            print("SFX file not found:", path)
    except Exception as e:
        print(f"SFX load error for {path}:", e)
    return None

# ----------------------------
# SETTINGS
# ----------------------------
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 740
LOWER_MARGIN = 100
SIDE_MARGIN = 300
FPS = 60
ROWS = 16
TILE_SIZE = SCREEN_HEIGHT // ROWS

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_ROOT  = PROJECT_ROOT / "assets"
ASSETS = PROJECT_ROOT / "assets" / "LevelEditor-main" / "LevelEditor-main" / "img"
TILE_ASSETS = ASSETS / "tile"
BG_ASSETS = ASSETS / "Background"
LEVEL_FILE = PROJECT_ROOT / "src" / "level.json"

# Colors
WHITE = (255, 255, 255)
GAME_BG = (30, 30, 30)

# ----------------------------
# INIT
# ----------------------------
pygame.init()
# Robust mixer init for WAV SFX
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
print("Mixer initialized:", pygame.mixer.get_init())

screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN))
pygame.display.set_caption("Run Red, Run!")
clock = pygame.time.Clock()

# Load SFX AFTER mixer init
sfx = {name: load_sfx(p) for name, p in SFX_PATHS.items()}
print("Loaded SFX:", [name for name, snd in sfx.items() if snd])

# ----------------------------
# LOAD BACKGROUND
# ----------------------------
def load_image_safe(path):
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except:
        surf = pygame.Surface((64,64))
        surf.fill((255,0,255))
        return surf

sky_img = load_image_safe(BG_ASSETS / "sky_cloud.png")
mountain_img = load_image_safe(BG_ASSETS / "mountain.png")
pine1_img = load_image_safe(BG_ASSETS / "pine1.png")
pine2_img = load_image_safe(BG_ASSETS / "pine2.png")

# ----------------------------
# LOAD TILES
# ----------------------------
img_list = []
tile_files = sorted(TILE_ASSETS.glob("*.png"))
if not tile_files:
    raise FileNotFoundError(f"No tile images found in {TILE_ASSETS}")
for tile_path in tile_files:
    img_list.append(load_image_safe(tile_path))

# ----------------------------
# LOAD PLAYER FRAMES
# ----------------------------
def load_frames(paths, scale=1.0):
    frames = []
    for p in paths:
        img = load_image_safe(p)
        if scale != 1.0:
            img = pygame.transform.scale(img, (int(img.get_width()*scale), int(img.get_height()*scale)))
        frames.append(img)
    return frames

PLAYER_SCALE = 2.0

PLAYER_IDLE_FRAMES = load_frames([ASSETS_ROOT / f"red_idle_{i}.png" for i in range(1,9)], PLAYER_SCALE)
PLAYER_RUN         = load_frames([ASSETS_ROOT / f"red_run_{i}.png"  for i in range(1,24)], PLAYER_SCALE)
PLAYER_CLIMB       = load_frames([ASSETS_ROOT / f"red_wallslide_{i}.png" for i in range(1,5)], PLAYER_SCALE)
PLAYER_JUMP        = load_frames([ASSETS_ROOT / f"red_jump_{i}.png" for i in range(1,13)], PLAYER_SCALE)
PLAYER_TURN        = load_frames([ASSETS_ROOT / f"red_turn_{i}.png" for i in range(1,3)], PLAYER_SCALE)

# ----------------------------
# WORLD
# ----------------------------
class World:
    def __init__(self):
        self.tile_list = []
        self.obstacle_list = []
        self.kill_list = []
        self.vine_list = []

    def process_data(self, data):
        self.tile_list = []
        self.obstacle_list = []
        for entry in data:
            tile_index = entry.get("tile_index", -1)
            grid_x = entry.get("x", 0)
            grid_y = entry.get("y", 0)
            scale = max(0.1, entry.get("scale", 1.0))
            if 0 <= tile_index < len(img_list):
                img = img_list[tile_index]
                new_size = (int(TILE_SIZE * scale), int(TILE_SIZE * scale))
                img = pygame.transform.scale(img, new_size)
                px = int(grid_x * TILE_SIZE)
                py = int(grid_y * TILE_SIZE)
                rect = pygame.Rect(px, py, img.get_width(), img.get_height())
                self.tile_list.append((img, rect))

                if tile_index == 5 or tile_index == 3 or (tile_index>=129 and tile_index<=133) or (tile_index>=58 and tile_index<=93):
                    self.obstacle_list.append((img, rect))
                if tile_index == 14:
                    kill_rect = rect.copy()
                    kill_rect.y -= int(TILE_SIZE * 0.025)
                    kill_rect.height += int(TILE_SIZE * 0.3)
                    self.kill_list.append((img, kill_rect))
                if 120 <= tile_index <= 123:
                    self.vine_list.append((img, rect))

    def draw(self, surf, scroll):
        for img, rect in self.tile_list:
            surf.blit(img, (rect.x - scroll, rect.y))

# ----------------------------
# PLAYER CLASS
# ----------------------------
GRAVITY = 0.85
JUMP_POWER = 11
BASELINE_Y = SCREEN_HEIGHT // 2
PLAYER_FOOT_OFFSET = 50

class Player(pygame.sprite.Sprite):
    def __init__(self, idle_frames, run_frames, climb_frames, jump_frames, turn_frames, x, baseline_y, foot_offset=0, speed=5):
        super().__init__()
        self.idle_frames = idle_frames
        self.run_frames = run_frames
        self.climb_frames = climb_frames
        self.jump_frames = jump_frames
        self.turn_frames = turn_frames
        self.turning = False
        self.turn_start_time = 0
        self.turn_duration = 300

        self.frame_index = 0
        self.image = self.idle_frames[0]
        self.rect = self.image.get_rect()
        self.baseline_y = baseline_y + foot_offset
        self.x = float(x)
        self.y = float(self.baseline_y)
        self.rect.midbottom = (int(self.x), int(self.y))
        self.flip = False
        self.speed = speed
        self.vel_y = 0.0
        self.airborne = False
        self.frame_time_ms = 1000 // 24
        self._last_update = pygame.time.get_ticks()
        self._current_seq = self.idle_frames

    def try_jump(self):
        if not self.airborne:
            self.vel_y = -JUMP_POWER
            self.airborne = True
            if sfx.get("jump"): sfx["jump"].play()

    def move_and_animate(self, dx, obstacles):
        # Horizontal
        self.x += dx
        self.rect.midbottom = (int(self.x), int(self.y))
        for _, rect in obstacles:
            if self.rect.colliderect(rect):
                if dx > 0:
                    step_height = rect.top - self.rect.bottom
                    if 0 < step_height <= TILE_SIZE * 0.3:
                        self.rect.bottom = rect.top
                        self.vel_y = 0
                        self.airborne = False
                    else:
                        self.rect.right = rect.left
                elif dx < 0:
                    step_height = rect.top - self.rect.bottom
                    if 0 < step_height <= TILE_SIZE * 0.3:
                        self.rect.bottom = rect.top
                        self.vel_y = 0
                        self.airborne = False
                    else:
                        self.rect.left = rect.right
                self.x = self.rect.midbottom[0]

        # Vertical
        self.vel_y += GRAVITY
        self.y += self.vel_y
        self.rect.midbottom = (int(self.x), int(self.y))
        for _, rect in obstacles:
            if self.rect.colliderect(rect):
                if self.vel_y > 0:
                    self.rect.bottom = rect.top
                    self.vel_y = 0
                    self.airborne = False
                elif self.vel_y < 0:
                    self.rect.top = rect.bottom
                    self.vel_y = 0
                self.y = self.rect.midbottom[1]

        # Turn
        if dx < 0 and not self.flip:
            self.turning = True
            self.turn_start_time = pygame.time.get_ticks()
            self.flip = True
        elif dx > 0 and self.flip:
            self.turning = True
            self.turn_start_time = pygame.time.get_ticks()
            self.flip = False

        # Anim state
        if self.turning:
            seq = self.turn_frames
            if pygame.time.get_ticks() - self.turn_start_time > self.turn_duration:
                self.turning = False
        elif self.airborne:
            seq = self.jump_frames
        elif dx != 0:
            seq = self.run_frames
        else:
            seq = self.idle_frames

        self.animate(seq)

    def animate(self, seq):
        if seq == self.run_frames:
            self.frame_time_ms = 1000 // 24
        else:
            self.frame_time_ms = 1000 // 12
        if seq != getattr(self, "_current_seq", None):
            self.frame_index = 0
            self._current_seq = seq
        if self._current_seq:
            now = pygame.time.get_ticks()
            if now - self._last_update > self.frame_time_ms:
                self._last_update = now
                self.frame_index = (self.frame_index + 1) % len(self._current_seq)
            self.image = self._current_seq[self.frame_index]
        old_midbottom = self.rect.midbottom
        self.rect = self.image.get_rect()
        self.rect.midbottom = old_midbottom
        self.x = float(self.rect.midbottom[0])
        self.y = float(self.rect.midbottom[1])

    def on_vine(self, vines):
        for _, r in vines:
            if self.rect.colliderect(r):
                return True
        return False

    def draw(self, surf, scroll):
        surf.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - scroll, self.rect.y))

# ----------------------------
# DIALOG + FADE CLASSES
# ----------------------------
class DialogBubble:
    def __init__(self, text, font, color, world_x, world_y):
        self.text = text
        self.font = font
        self.color = color
        self.world_x = world_x
        self.world_y = world_y
        self.current_text = ""
        self.index = 0
        self.active = False
        self.last_update = 0
        self.delay = 60

    def start(self):
        self.active = True
        self.index = 0
        self.current_text = ""
        self.last_update = pygame.time.get_ticks()

    def update(self):
        if self.active and self.index < len(self.text):
            now = pygame.time.get_ticks()
            if now - self.last_update > self.delay:
                self.current_text += self.text[self.index]
                self.index += 1
                self.last_update = now

    def draw(self, surf, scroll):
        if not self.active:
            return
        x = int(self.world_x - scroll)
        y = int(self.world_y)
        bubble_rect = pygame.Rect(x - 20, y - 70, 320, 60)
        pygame.draw.rect(surf, (255, 255, 255), bubble_rect, border_radius=12)
        pygame.draw.rect(surf, (0, 0, 0), bubble_rect, 2, border_radius=12)
        pygame.draw.polygon(
            surf, (255, 255, 255),
            [(bubble_rect.x + 40, bubble_rect.bottom),
             (bubble_rect.x + 60, bubble_rect.bottom + 20),
             (bubble_rect.x + 80, bubble_rect.bottom)]
        )
        pygame.draw.polygon(
            surf, (0, 0, 0),
            [(bubble_rect.x + 40, bubble_rect.bottom),
             (bubble_rect.x + 60, bubble_rect.bottom + 20),
             (bubble_rect.x + 80, bubble_rect.bottom)], 2
        )
        txt_surf = self.font.render(self.current_text, True, self.color)
        surf.blit(txt_surf, (bubble_rect.x + 10, bubble_rect.y + 15))

class FadeEffect:
    def __init__(self, w, h, speed=5):
        self.surface = pygame.Surface((w, h))
        self.surface.fill((0, 0, 0))
        self.alpha = 0
        self.speed = speed
        self.active = False
        self.done = False

    def start(self):
        self.active = True
        self.alpha = 0
        self.done = False

    def update(self):
        if self.active and not self.done:
            self.alpha += self.speed
            if self.alpha >= 255:
                self.alpha = 255
                self.done = True
            self.surface.set_alpha(self.alpha)

    def draw(self, surf):
        if self.active:
            surf.blit(self.surface, (0, 0))

# NEW: top-to-bottom fade for Game Over
class FadeDown:
    def __init__(self, w, h, speed=8):
        self.surface = pygame.Surface((w, h))
        self.surface.fill((0, 0, 0))
        self.h = h
        self.speed = speed
        self.height = 0
        self.active = False
        self.done = False

    def start(self):
        self.active = True
        self.done = False
        self.height = 0

    def update(self):
        if self.active and not self.done:
            self.height += self.speed
            if self.height >= self.h:
                self.height = self.h
                self.done = True

    def draw(self, surf):
        if self.active:
            surf.blit(self.surface, (0, 0), area=pygame.Rect(0, 0, self.surface.get_width(), self.height))

# ----------------------------
# MAIN LOOP
# ----------------------------
def main():
    scroll = 0
    moving_left = moving_right = False

    play_game_music()
    wolf_timer = pygame.time.get_ticks()

    if LEVEL_FILE.exists():
        with open(LEVEL_FILE, "r") as f:
            level_data = json.load(f)
    else:
        level_data = []

    world_instance = World()
    world_instance.process_data(level_data)

    player = Player(PLAYER_IDLE_FRAMES, PLAYER_RUN, PLAYER_CLIMB, PLAYER_JUMP, PLAYER_TURN, 100, BASELINE_Y, PLAYER_FOOT_OFFSET)

    font = pygame.font.SysFont("arial", 24, bold=True)
    HOUSE_ZONE_MIN = 269 * TILE_SIZE
    HOUSE_ZONE_MAX = 272 * TILE_SIZE
    HOUSE_BUBBLE_X = 270 * TILE_SIZE + (TILE_SIZE * 1.0)
    HOUSE_BUBBLE_Y = (-3 + 11.4) * TILE_SIZE - (TILE_SIZE * 1.9)

    dialog = DialogBubble("Granny: Welcome dear, come in!", font, (0, 0, 0), HOUSE_BUBBLE_X, HOUSE_BUBBLE_Y)
    fade = FadeEffect(SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN, speed=5)
    end_sequence = False
    showed_complete = False
    idle_start_time = 0

    # Game-over state
    dead = False
    lose_fade = FadeDown(SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN, speed=10)
    restart_button_rect = None

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(GAME_BG)
        dx = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Handle restart click even when dead
            if event.type == pygame.MOUSEBUTTONDOWN and dead and restart_button_rect and restart_button_rect.collidepoint(event.pos):
                # Restart whole level cleanly
                main()
                return
            if not dead:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a: moving_left = True
                    if event.key == pygame.K_d: moving_right = True
                    if event.key in (pygame.K_w, pygame.K_SPACE): player.try_jump()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a: moving_left = False
                    if event.key == pygame.K_d: moving_right = False

        if not fade.active and not dead:
            dx = (-player.speed if moving_left else player.speed if moving_right else 0)
        else:
            dx = 0

        screen_center_x = SCREEN_WIDTH // 2
        player_screen_x = player.x - scroll
        if not dead:
            if player_screen_x > screen_center_x and dx > 0:
                scroll += dx
            elif player_screen_x < screen_center_x and dx < 0:
                scroll += dx
        scroll = max(0, scroll)

        # Background layers
        for i in range(16):
            offset_x = i * sky_img.get_width()
            screen.blit(sky_img, (offset_x - scroll * 0.4, 0))
            screen.blit(mountain_img, (offset_x - scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 260))
            screen.blit(pine1_img, (offset_x - scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 100))
            screen.blit(pine2_img, (offset_x - scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height() + 20))

        world_instance.draw(screen, scroll)

        if not dead:
            player.move_and_animate(dx, world_instance.obstacle_list)

            # Vine climbing (SFX REMOVED; logic intact)
            on_vine = player.on_vine(world_instance.vine_list)
            keys = pygame.key.get_pressed()
            if on_vine:
                player.animate(player.climb_frames)
                climb_speed = player.speed * 0.6
                moving_vertically = False
                if keys[pygame.K_w]:
                    player.y -= climb_speed
                    player.vel_y = 0
                    player.airborne = False
                    moving_vertically = True
                    # (vine sound removed)
                elif keys[pygame.K_s]:
                    player.y += climb_speed
                    player.vel_y = 0
                    player.airborne = False
                    moving_vertically = True
                    # (vine sound removed)
                player.rect.midbottom = (int(player.x), int(player.y))
                for _, rect in world_instance.obstacle_list:
                    if player.rect.colliderect(rect):
                        if keys[pygame.K_w]:
                            player.rect.top = rect.bottom
                            player.y = player.rect.midbottom[1]
                        elif keys[pygame.K_s]:
                            player.rect.bottom = rect.top
                            player.y = player.rect.midbottom[1]
                if not moving_vertically:
                    player.airborne = True

            # Kill → GAME OVER flow
            for _, rect in world_instance.kill_list:
                if player.rect.colliderect(rect):
                    dead = True
                    moving_left = moving_right = False
                    pygame.mixer.music.stop()          # stop background music immediately
                    if sfx.get("lose"): sfx["lose"].play()
                    lose_fade.start()
                    break

            # --- Ending scene ---
            if (not end_sequence) and (HOUSE_ZONE_MIN <= player.x <= HOUSE_ZONE_MAX):
                if sfx.get("win"): 
                    pygame.mixer.music.stop()          # stop background music on win start
                    sfx["win"].play()
                end_sequence = True
                moving_left = moving_right = False
                idle_start_time = pygame.time.get_ticks()

            if end_sequence and not dialog.active:
                if pygame.time.get_ticks() - idle_start_time > 1000:
                    dialog.start()

            if end_sequence:
                dialog.update()
                dialog.draw(screen, scroll)
                if dialog.active and dialog.index >= len(dialog.text) and not fade.active:
                    fade.start()

        fade.update()
        fade.draw(screen)

        if fade.done and not showed_complete:
            showed_complete = True

        if showed_complete:
            title_font = pygame.font.SysFont("arial", 60, bold=True)
            msg = title_font.render("Level #1 Complete!", True, (255, 255, 255))
            rect = msg.get_rect(center=((SCREEN_WIDTH + SIDE_MARGIN) // 2, (SCREEN_HEIGHT + LOWER_MARGIN) // 2))
            screen.blit(msg, rect)

        # Draw player every frame (even when dead, to keep last pose)
        player.draw(screen, scroll)

        # Wolf howl after 7s (play once)
        if sfx.get("wolfhowl") and pygame.time.get_ticks() - wolf_timer > 7000:
            sfx["wolfhowl"].play()
            sfx["wolfhowl"] = None

        # --- GAME OVER overlay & restart (only when dead) ---
        if dead:
            # Top-down fade first
            lose_fade.update()
            lose_fade.draw(screen)

            # Big GAME OVER on top (visible over fade)
            go_font = pygame.font.SysFont("arial", 120, bold=True)  # swap to your pixel font if you have it
            go_text = go_font.render("GAME OVER", True, (255, 0, 0))
            go_rect = go_text.get_rect(center=((SCREEN_WIDTH + SIDE_MARGIN) // 2, (SCREEN_HEIGHT + LOWER_MARGIN) // 2 - 80))
            screen.blit(go_text, go_rect)

            # After fade finishes, show clickable button
            if lose_fade.done:
                btn_font = pygame.font.SysFont("arial", 48, bold=True)
                btn_text = btn_font.render("Restart Level", True, (255, 255, 255))
                btn_rect = btn_text.get_rect(center=((SCREEN_WIDTH + SIDE_MARGIN) // 2, (SCREEN_HEIGHT + LOWER_MARGIN) // 2 + 80))
                pad = 20
                bg_rect = btn_rect.inflate(pad * 2, pad * 2)
                pygame.draw.rect(screen, (50, 50, 50), bg_rect, border_radius=12)
                pygame.draw.rect(screen, (200, 200, 200), bg_rect, 2, border_radius=12)
                screen.blit(btn_text, btn_rect)
                restart_button_rect = bg_rect

        pygame.display.flip()

    pygame.mixer.music.fadeout(2000)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
