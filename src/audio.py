# audio.py
import pygame
from asset_loader import ASSETS
from settings import MENU_VOLUME, GAME_VOLUME

MENU_MUSIC = ASSETS / "Video-Project.ogg"  # menu track you added
GAME_MUSIC = ASSETS / "game_loop.ogg"      # optional gameplay track

def init_audio():
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

def play_menu_music(start_at=3.0):
    if MENU_MUSIC.is_file():
        pygame.mixer.music.load(str(MENU_MUSIC))
        pygame.mixer.music.set_volume(MENU_VOLUME)
        pygame.mixer.music.play(-1, start_at)

def play_game_music(start_at=3.0):
    if GAME_MUSIC.is_file():
        pygame.mixer.music.load(str(GAME_MUSIC))
        pygame.mixer.music.set_volume(GAME_VOLUME)
        pygame.mixer.music.play(-1, start_at, fade_ms=600)
    else:
        pygame.mixer.music.fadeout(500)

def fade_out(ms=500):
    pygame.mixer.music.fadeout(ms)

