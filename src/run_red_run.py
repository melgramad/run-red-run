import pygame
import csv
import sys
import json
from pathlib import Path

pygame.init()
import glob
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parent


# where the editor writes its CSVs (same folder as the game by default)
LEVELS_DIR = ROOT

LEVEL_RE = re.compile(r"level(\d+)_data\.csv$", re.IGNORECASE)

def list_available_levels():
    files = sorted(LEVELS_DIR.glob("level*_data.csv"))
    levels = []
    for f in files:
        m = LEVEL_RE.search(f.name)
        if m:
            levels.append(int(m.group(1)))
    return sorted(set(levels))

def load_level_into(world_data, level_num):
    """
    Tries, in order:
    1) level{n}_data.csv (correct name)
    2) level{n}.data.csv (common typo with a dot)
    """
    candidates = [
        LEVELS_DIR / f"level{level_num}_data.csv",   # correct
        LEVELS_DIR / f"level{level_num}.data.csv",   # typo fallback
    ]
    for fp in candidates:
        if fp.is_file():
            with open(fp, newline="") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                for x, row in enumerate(reader):
                    for y, tile in enumerate(row):
                        world_data[x][y] = int(tile)
            print(f"[OK] Loaded {fp.name}")
            return True
    return False

# --- init world, then try to load; if missing, fall back gracefully ---
ROWS = 16
MAX_COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
world_data = [[-1]*MAX_COLS for _ in range(ROWS)]

level = 0  # start from what you actually saved in the editor
if not load_level_into(world_data, level):
    avail = list_available_levels()
    if avail:
        print(f"[WARN] level{level}_data.csv not found. Available levels: {avail}. Loading level{avail[0]}.")
        load_level_into(world_data, avail[0])
        level = avail[0]
    else:
        print("[WARN] No level*_data.csv files found. Run the editor and Save a level first.")


# --- Screen Setup ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Run, Red, Run!")

clock = pygame.time.Clock()

# --- Game Variables ---
ROWS = 16
MAX_COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
level = 0
scroll = 0
scroll_speed = 4

# --- Paths ---
ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "img"
BG_DIR = IMG_DIR / "Background"
TILE_DIR = IMG_DIR / "tile"

# --- Load Background Images ---
sky_img = pygame.image.load(str(BG_DIR / "sky_cloud.png")).convert_alpha()
mountain_img = pygame.image.load(str(BG_DIR / "mountain.png")).convert_alpha()
pine1_img = pygame.image.load(str(BG_DIR / "pine1.png")).convert_alpha()
pine2_img = pygame.image.load(str(BG_DIR / "pine2.png")).convert_alpha()

# --- Load Tiles ---
TILE_TYPES = 21
tile_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(str(TILE_DIR / f"{x}.png")).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    tile_list.append(img)

# --- Colors ---
WHITE = (255, 255, 255)
GREEN = (144, 201, 120)

# --- Font ---
font = pygame.font.SysFont("Futura", 30)

# --- World Data ---
world_data = [[-1] * MAX_COLS for _ in range(ROWS)]

# --- Load Level Function ---
def load_level(level):
    filename = f"level{level}_data.csv"
    try:
        with open(filename, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    world_data[x][y] = int(tile)
        print(f"[OK] Loaded {filename}")
    except FileNotFoundError:
        print(f"[WARN] Level file {filename} not found — starting empty.")

# --- Draw Background ---
def draw_bg():
    screen.fill(GREEN)
    width = sky_img.get_width()
    for x in range(4):
        screen.blit(sky_img, ((x * width) - scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - scroll * 0.6,
                                   SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - scroll * 0.7,
                                SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - scroll * 0.8,
                                SCREEN_HEIGHT - pine2_img.get_height()))

# --- Draw World Tiles ---
def draw_world():
    for y, row in enumerate(world_data):
        for x, tile in enumerate(row):
            if tile >= 0:
                screen.blit(tile_list[tile], (x * TILE_SIZE - scroll, y * TILE_SIZE))

# --- Draw Text ---
def draw_text(text, x, y, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

# --- Player Setup (simple rectangle placeholder) ---
player_rect = pygame.Rect(100, SCREEN_HEIGHT - TILE_SIZE * 2, TILE_SIZE, TILE_SIZE * 2)
player_vel_y = 0
on_ground = False
GRAVITY = 1.5
MOVE_SPEED = 5
JUMP_FORCE = 12

# --- Game State ---
load_level(level)
moving_left = moving_right = False

# --- Main Loop ---
run = True
while run:
    clock.tick(FPS)
    draw_bg()
    draw_world()

    # --- Player Movement ---
    dx = 0
    dy = player_vel_y

    if moving_left:
        dx = -MOVE_SPEED
    if moving_right:
        dx = MOVE_SPEED

    # gravity
    player_vel_y += GRAVITY
    if player_vel_y > 10:
        player_vel_y = 10

    # floor collision
    if player_rect.bottom + player_vel_y >= SCREEN_HEIGHT:
        player_vel_y = 0
        player_rect.bottom = SCREEN_HEIGHT
        on_ground = True
    else:
        on_ground = False

    player_rect.x += dx
    player_rect.y += player_vel_y

    # --- Draw Player ---
    pygame.draw.rect(screen, (255, 0, 0), player_rect)

    # --- HUD ---
    draw_text(f"Level: {level}", 10, 10)
    draw_text("← / → Move   ↑ Jump   L / R Scroll   PgUp/PgDn Change Level", 10, 40)

    # --- Events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                moving_left = True
            if event.key == pygame.K_RIGHT:
                moving_right = True
            if event.key == pygame.K_UP and on_ground:
                player_vel_y = -JUMP_FORCE
                on_ground = False
            if event.key == pygame.K_L:
                scroll = max(0, scroll - TILE_SIZE * 2)
            if event.key == pygame.K_R:
                scroll += TILE_SIZE * 2
            if event.key == pygame.K_PAGEUP:
                level += 1
                load_level(level)
            if event.key == pygame.K_PAGEDOWN and level > 0:
                level -= 1
                load_level(level)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                moving_left = False
            if event.key == pygame.K_RIGHT:
                moving_right = False

    pygame.display.update()

pygame.quit()
sys.exit()
