# settings.py
from pathlib import Path

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
FPS = 60

# Colors
GAME_BG = (30, 30, 30)
MENU_BG = (85, 22, 22)  # deep, nearly-black crimson

# Root of your asset tree (adjust to your layout)
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_ROOT  = PROJECT_ROOT / "assets"

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
