import sys 
from pathlib import Path
import pygame
import json
import csv
pygame.init()

SHARED_FOLDER = Path("C:/Dev/orgsOfLangs/run-red-run")
LEVEL_FILE = SHARED_FOLDER / "src" / "level.json"


clock = pygame.time.Clock()
FPS = 60

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "LevelEditor-main" / "LevelEditor-main" / "img"

BG_ASSETS = ASSETS / "Background"
TILE_ASSETS = ASSETS / "tile"

SKY = BG_ASSETS / "sky_cloud.png"
MOUNTAIN = BG_ASSETS / "mountain.png"
PINE1 = BG_ASSETS / "pine1.png"
PINE2 = BG_ASSETS / "pine2.png"

SAVE_BTN = ASSETS / "save_btn.png"
LOAD_BTN = ASSETS / "load_btn.png"

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 740
LOWER_MARGIN = 100
SIDE_MARGIN = 300

screen = pygame.display.set_mode(
    (SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN)
)
pygame.display.set_caption("Level Editor")

WHITE = (255, 255, 255)

ROWS = 16
MAX_COLS = 500
TILE_SIZE = SCREEN_HEIGHT // ROWS

scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 25

tile_scale = 1.0
scale_step = 0.1
max_scale = 15.0
min_scale = 0.5

sky_img = pygame.image.load(str(SKY)).convert_alpha()
mountain_img = pygame.image.load(str(MOUNTAIN)).convert_alpha()
pine1_img = pygame.image.load(str(PINE1)).convert_alpha()
pine2_img = pygame.image.load(str(PINE2)).convert_alpha()

img_list = []
tile_files = sorted(TILE_ASSETS.glob("*.png"))
if not tile_files:
    raise FileNotFoundError(f"No tile images found in {TILE_ASSETS}")

for tile_path in tile_files:
    img = pygame.image.load(str(tile_path)).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

TILE_TYPES = len(img_list)

save_btn_img = pygame.image.load(str(SAVE_BTN)).convert_alpha()
save_btn_img = pygame.transform.scale(save_btn_img, (100, 50))
load_btn_img = pygame.image.load(str(LOAD_BTN)).convert_alpha()
load_btn_img = pygame.transform.scale(load_btn_img, (100, 50))

GAME_MUSIC = Path(r"C:\Dev\KingdomDance.m4a")

def play_game_music():
    try:
        if GAME_MUSIC.exists():
            pygame.mixer.music.load(str(GAME_MUSIC))
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play(-1, start=0.0)  # loops until exit
        else:
            print("Game music not found:", GAME_MUSIC)
    except Exception as e:
        print("Audio error:", e)



class TileButton:
    def __init__(self, image, x, y, size, index):
        self.image = pygame.transform.scale(image, (size, size))
        self.rect = pygame.Rect(x, y, size, size)
        self.index = index

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
        pygame.draw.rect(surface, WHITE, self.rect, 1)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Button:
    def __init__(self, image, x, y):
        self.image = image
        self.rect = pygame.Rect(x, y, image.get_width(), image.get_height())

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
        pygame.draw.rect(surface, WHITE, self.rect, 1)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

tile_buttons = []
button_size = 30
padding = 10
cols = 7

for i, img in enumerate(img_list):
    col = i % cols
    row = i // cols
    x = SCREEN_WIDTH + padding + col * (button_size + padding)
    y = padding + row * (button_size + padding)
    tile_buttons.append(TileButton(img, x, y, button_size, i))

selected_tile_index = None
placed_tiles = []

load_button = Button(load_btn_img, SCREEN_WIDTH - 1000, SCREEN_HEIGHT - -30)
save_button = Button(save_btn_img, SCREEN_WIDTH - 200, SCREEN_HEIGHT - -30)


def draw_bg():
    for i in range(17):
        offset_x = (i * sky_img.get_width()) - scroll
        screen.blit(sky_img, (offset_x - scroll * 0.4, 0))
        screen.blit(
            mountain_img,
            (offset_x - scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 260),
        )
        screen.blit(
            pine1_img,
            (offset_x - scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 100),
        )
        screen.blit(
            pine2_img,
            (offset_x - scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height() + 20),
        )

def draw_grid():
    for c in range(MAX_COLS + 1):
        pygame.draw.line(
            screen,
            WHITE,
            (c * TILE_SIZE - scroll, 0),
            (c * TILE_SIZE - scroll, SCREEN_HEIGHT),
        )
    for r in range(ROWS + 1):
        pygame.draw.line(
            screen, WHITE, (0, r * TILE_SIZE), (SCREEN_WIDTH, r * TILE_SIZE)
        )

run = True
while run:
    clock.tick(FPS)
    screen.fill((0, 0, 0))

    draw_bg()
    draw_grid()

    for tile_index, x, y, scale in placed_tiles:
        tile_img = img_list[tile_index]
        scaled_size = int(TILE_SIZE * scale)
        scaled_img = pygame.transform.scale(tile_img, (scaled_size, scaled_size))
        screen.blit(scaled_img, (x * TILE_SIZE - scroll, y * TILE_SIZE))

    for button in tile_buttons:
        button.draw(screen)

    save_button.draw(screen)
    load_button.draw(screen)

    if selected_tile_index is not None:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_img = img_list[selected_tile_index]
        scaled_size = int(TILE_SIZE * tile_scale)
        scaled_img = pygame.transform.scale(tile_img, (scaled_size, scaled_size))

        if mouse_x < SCREEN_WIDTH:
            snap_x = (mouse_x // TILE_SIZE) * TILE_SIZE
            snap_y = (mouse_y // TILE_SIZE) * TILE_SIZE
            screen.blit(scaled_img, (snap_x, snap_y))
        else:
            screen.blit(
                scaled_img, (mouse_x - scaled_size // 2, mouse_y - scaled_size // 2)
            )

    if scroll_left:
        scroll -= scroll_speed
    if scroll_right:
        scroll += scroll_speed
    MAX_SCROLL = 11500
    scroll = max(0, min(scroll, MAX_SCROLL))
    #scroll = max(0, min(scroll, (sky_img.get_width() * 45) - SCREEN_WIDTH))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                scroll_left = True
            if event.key == pygame.K_RIGHT:
                scroll_right = True
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                tile_scale = min(max_scale, tile_scale + scale_step)
            if event.key == pygame.K_MINUS:
                tile_scale = max(min_scale, tile_scale - scale_step)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if event.button == 1:
                for button in tile_buttons:
                    if button.is_clicked(mouse_pos):
                        selected_tile_index = button.index

                if selected_tile_index is not None and mouse_pos[0] < SCREEN_WIDTH:
                    grid_x = (mouse_pos[0] + scroll) // TILE_SIZE
                    grid_y = mouse_pos[1] // TILE_SIZE
                    placed_tiles.append(
                        (selected_tile_index, grid_x, grid_y, tile_scale)
                    )

                # --- Save ---
                if save_button.is_clicked(mouse_pos):
                    # Save as a list of dicts for clarity
                    save_data = [
                        {
                            "tile_index": tile_index,
                            "x": x,
                            "y": y,
                            "scale": scale
                        }
                        for tile_index, x, y, scale in placed_tiles
                    ]
                    with open(LEVEL_FILE, "w") as f:
                        json.dump(save_data, f, indent=4)  # indent makes it easier to edit manually
                    #print(f"Saved {len(placed_tiles)} tiles to {LEVEL_FILE}")

                # --- Load ---
                elif load_button.is_clicked(mouse_pos):
                    #print(f"Attempting to load {LEVEL_FILE}")
                    if LEVEL_FILE.is_file():
                        with open(LEVEL_FILE, "r") as f:
                            loaded_tiles = json.load(f)
                        #print(f"Raw loaded data: {loaded_tiles}")

                        placed_tiles.clear()

                        for item in loaded_tiles:
                            # Handle dict format
                            if isinstance(item, dict):
                                tile_index = item.get("tile_index", 0)
                                x = item.get("x", 0)
                                y = item.get("y", 0)
                                scale = item.get("scale", 1.0)
                                placed_tiles.append((tile_index, x, y, scale))
                            # Handle old list format: [tile_index, x, y, scale] or [x, y, tile_index]
                            elif isinstance(item, list):
                                if len(item) == 4:
                                    tile_index, x, y, scale = item
                                    placed_tiles.append((tile_index, x, y, scale))
                                elif len(item) == 3:
                                    x, y, tile_index = item
                                    placed_tiles.append((tile_index, x, y, 1.0))
                       # print(f"Loaded {len(placed_tiles)} tiles successfully")
                    else:
                        print("No level.json file found!")





            if event.button == 3 and mouse_pos[0] < SCREEN_WIDTH:
                grid_x = (mouse_pos[0] + scroll) // TILE_SIZE
                grid_y = mouse_pos[1] // TILE_SIZE
                placed_tiles = [
                    (t_index, x, y, s)
                    for t_index, x, y, s in placed_tiles
                    if not (x == grid_x and y == grid_y)
                ]

    pygame.display.update()

pygame.quit()
