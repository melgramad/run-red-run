import sys, pygame, importlib
from pathlib import Path

# ----------------------------
# SETTINGS
# ----------------------------
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 740
FPS = 60
MENU_BG = (85, 22, 22)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_ROOT = PROJECT_ROOT / "assets"

# ----------------------------
# INIT
# ----------------------------
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Run Red, Run!")
clock = pygame.time.Clock()

# ----------------------------
# UI ELEMENTS
# ----------------------------
def _font(sz, bold=False): 
    return pygame.font.SysFont("comic sans ms", sz, bold=bold)

TITLE = _font(64)
BTN = _font(36)

def draw_button(surf, rect, text, mouse_pos):
    hovered = rect.collidepoint(mouse_pos)
    base = (60, 60, 60) if not hovered else (90, 90, 90)
    border = (180, 180, 180)
    pygame.draw.rect(surf, base, rect, border_radius=12)
    pygame.draw.rect(surf, border, rect, width=2, border_radius=12)
    label = BTN.render(text, True, (230, 230, 230))
    surf.blit(label, label.get_rect(center=rect.center))

# ----------------------------
# PLAYER (Red) FOR MENU
# ----------------------------
def _placeholder(w=64, h=64, text="missing"):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((90, 30, 30))
    pygame.draw.rect(s, (200, 60, 60), s.get_rect(), 3)
    lbl = pygame.font.SysFont(None, 16).render(text, True, (230, 230, 230))
    s.blit(lbl, lbl.get_rect(center=s.get_rect().center))
    return s

def load_frames(prefix, start, end, scale=2.0):
    frames = []
    for i in range(start, end + 1):
        p = ASSETS_ROOT / f"{prefix}{i}.png"
        try:
            img = pygame.image.load(str(p)).convert_alpha()
            if scale != 1.0:
                img = pygame.transform.scale(img, (int(img.get_width()*scale), int(img.get_height()*scale)))
            frames.append(img)
        except Exception:
            frames.append(_placeholder(int(32*scale), int(32*scale), f"{prefix}{i}"))
    return frames if frames else [_placeholder(64, 64, "no_frames")]

class PlayerMenu(pygame.sprite.Sprite):
    def __init__(self, idle_frames, x, baseline_y, anim_fps=10):
        super().__init__()
        self.frames = idle_frames or []
        self.idx = 0
        self.image = self.frames[0] if self.frames else _placeholder()
        self.rect = self.image.get_rect(midbottom=(x, baseline_y))
        self.last = pygame.time.get_ticks()
        self.step = 1000 // max(1, anim_fps)
        self.x, self.y = float(self.rect.centerx), float(self.rect.bottom)

    def update(self):
        if not self.frames: return
        now = pygame.time.get_ticks()
        if now - self.last >= self.step:
            self.last = now
            self.idx = (self.idx + 1) % len(self.frames)
            self.image = self.frames[self.idx]
            self.rect = self.image.get_rect(midbottom=(int(self.x), int(self.y)))

    def draw(self, surf):
        surf.blit(self.image, self.rect)

# ----------------------------
# AUDIO (your same file)
# ----------------------------
MENU_MUSIC = ASSETS_ROOT / "Video-Project.ogg"

def play_menu_music():
    try:
        if MENU_MUSIC.exists():
            pygame.mixer.music.load(str(MENU_MUSIC))
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play(-1, start=3.0)
    except Exception as e:
        print("Audio error:", e)

# ----------------------------
# MAIN MENU
# ----------------------------
def main():
    title = TITLE.render("Run Red, Run!", True, (230, 230, 230))
    start_rect = pygame.Rect(0, 0, 240, 56)
    start_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//3)
    exit_rect = pygame.Rect(0, 0, 240, 56)
    exit_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 80)

    idle = load_frames("red_idle_", 1, 8, scale=2.8)
    menu_red = PlayerMenu(idle, x=SCREEN_WIDTH//2, baseline_y=SCREEN_HEIGHT//2 + 220)

    play_menu_music()

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if start_rect.collidepoint(e.pos):
                    pygame.mixer.music.stop()
                    # direct launch
                    spec = importlib.util.spec_from_file_location("BG", (Path(__file__).parent / "BG.py"))
                    BG = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(BG)
                    BG.main()
                    play_menu_music()
                elif exit_rect.collidepoint(e.pos):
                    running = False

        screen.fill(MENU_BG)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//6)))
        mp = pygame.mouse.get_pos()
        draw_button(screen, start_rect, "Start", mp)
        draw_button(screen, exit_rect, "Exit", mp)
        menu_red.update()
        menu_red.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
