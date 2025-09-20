from pathlib import Path
import pygame

# project root = one level above src/
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

def load_frames(paths, scale=3.0):
    frames = []
    for p in paths:
        img = pygame.image.load(str(p)).convert_alpha()
        img = pygame.transform.scale(
            img, (int(img.get_width() * scale), int(img.get_height() * scale))
        )
        frames.append(img)
    return frames

def verify_sequence(prefix, start, end, ext=".png"):
    missing = [f"{prefix}{i}{ext}" for i in range(start, end + 1)
               if not (ASSETS / f"{prefix}{i}{ext}").is_file()]
    if missing:
        raise FileNotFoundError(f"Missing frames: {missing} in {ASSETS}")

def load_numbered(prefix, start, end, ext=".png", scale=1.0):
    verify_sequence(prefix, start, end, ext)  # friendly error if anything missing
    files = [ASSETS / f"{prefix}{i}{ext}" for i in range(start, end + 1)]
    return load_frames(files, scale)

