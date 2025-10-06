#main
import pygame
pygame.init()  # init BEFORE importing ui (fonts)

import settings
from asset_loader import ASSETS, load_frames, load_numbered
import audio
from entities import Player, WolfStatic, IdleBreather
from ui import draw_button, render_title, draw_timer

audio.init_audio()

# ---------- WINDOW ----------
screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
pygame.display.set_caption("Run, Red, Run!")
clock = pygame.time.Clock()

# ---------- FRAME NORMALIZER ----------
def normalize_frames(frames, anchor="midbottom"):
    if not frames:
        return frames
    max_w = max(f.get_width()  for f in frames)
    max_h = max(f.get_height() for f in frames)
    norm = []
    for f in frames:
        r = f.get_rect()
        if   anchor == "midbottom": an = r.midbottom
        elif anchor == "midtop":    an = r.midtop
        elif anchor == "midleft":   an = r.midleft
        elif anchor == "midright":  an = r.midright
        elif anchor == "center":    an = r.center
        else:                       an = r.midbottom
        canvas = pygame.Surface((max_w, max_h), pygame.SRCALPHA, 32).convert_alpha()
        dst_r = canvas.get_rect()
        if   anchor == "midbottom": dst_anchor = dst_r.midbottom
        elif anchor == "midtop":    dst_anchor = dst_r.midtop
        elif anchor == "midleft":   dst_anchor = dst_r.midleft
        elif anchor == "midright":  dst_anchor = dst_r.midright
        elif anchor == "center":    dst_anchor = dst_r.center
        else:                       dst_anchor = dst_r.midbottom
        ox = dst_anchor[0] - an[0]
        oy = dst_anchor[1] - an[1]
        canvas.blit(f, (ox, oy))
        norm.append(canvas)
    return norm

# ---------- ART ----------
PLAYER_IDLE_FRAMES = load_numbered("red_idle_", 1 , 8, scale=2.0)
PLAYER_RUN         = load_numbered("red_run_",  1, 23, scale=2.0)
WOLF_IDLE          = load_frames([ASSETS / "wolf_stand_1.png"], scale=1.5)[0]
WOLF_RUN           = load_numbered("wolf_run_", 1, 9, scale=1.5)

PLAYER_IDLE_FRAMES = normalize_frames(PLAYER_IDLE_FRAMES, anchor="midbottom")
PLAYER_RUN         = normalize_frames(PLAYER_RUN,         anchor="midbottom")

# ---------- ENTITIES ----------
player = Player(
    PLAYER_IDLE_FRAMES, PLAYER_RUN,
    x=320, baseline_y=settings.BASELINE_Y,
    foot_offset=settings.PLAYER_FOOT_OFFSET,
    speed=5, anim_fps=10
)
wolf = WolfStatic(
    WOLF_RUN, WOLF_IDLE,
    left_x=settings.WOLF_EDGE_X,
    baseline_y=settings.BASELINE_Y,
    foot_offset=settings.WOLF_FOOT_OFFSET,
    anim_fps=12, flip=False
)

player.rect.left = max(wolf.rect.right + settings.STARTING_GAP, player.rect.left)
player.x = player.rect.midbottom[0]

# ---------- MENU SETUP ----------
state = "menu"
audio.play_menu_music()

title_surf = render_title("Run Red, Run!")
btn_w, btn_h = 240, 56
start_rect = pygame.Rect(0, 0, btn_w, btn_h)
exit_rect  = pygame.Rect(0, 0, btn_w, btn_h)
start_rect.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 3)
exit_rect.center  = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 3 + 80)

menu_red = IdleBreather(
    PLAYER_IDLE_FRAMES,
    x=settings.SCREEN_WIDTH // 2,
    baseline_y=exit_rect.bottom + 140,
    anim_fps=10
)

moving_left = moving_right = False
game_over = False

# ---------- TIMER ----------
timer_start_ms = None
elapsed_ms = 0

# ---------- MAIN LOOP ----------
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); raise SystemExit

        if state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_rect.collidepoint(event.pos):
                    state = "game"
                    audio.play_game_music()
                    timer_start_ms = pygame.time.get_ticks()
                    elapsed_ms = 0
                elif exit_rect.collidepoint(event.pos):
                    pygame.quit(); raise SystemExit
        else:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); raise SystemExit
                if not game_over:
                    if event.key == pygame.K_a: moving_left = True
                    elif event.key == pygame.K_d: moving_right = True
                    elif event.key in (pygame.K_w, pygame.K_SPACE):
                        player.try_jump()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a: moving_left = False
                elif event.key == pygame.K_d: moving_right = False

    if state == "menu":
        screen.fill(settings.MENU_BG)
        screen.blit(title_surf, title_surf.get_rect(
            center=(settings.SCREEN_WIDTH//2, settings.SCREEN_HEIGHT//6)))
        mouse_pos = pygame.mouse.get_pos()
        draw_button(screen, start_rect, "Start", mouse_pos)
        draw_button(screen, exit_rect,  "Exit",  mouse_pos)
        menu_red.update(); menu_red.draw(screen)

    else:
        screen.fill(settings.GAME_BG)

        if not game_over:
            if timer_start_ms is not None:
                now = pygame.time.get_ticks()
                elapsed_ms = now - timer_start_ms

            p_dx = (-player.speed if moving_left and not moving_right
                    else player.speed if moving_right and not moving_left
                    else 0)

            wolf.set_running(p_dx != 0)
            wolf.update()

            next_left = player.rect.left + p_dx
            contact_line = wolf.rect.right
            if next_left <= contact_line:
                game_over = True
                player.rect.left = contact_line
                player.x = player.rect.midbottom[0]
                player.move_and_animate(0)
            else:
                player.move_and_animate(p_dx)

            player.rect.right = max(0, min(player.rect.right, settings.SCREEN_WIDTH))
            player.x = player.rect.midbottom[0]

        wolf.draw(screen)
        player.draw(screen)

        total_sec = elapsed_ms // 1000
        mm = total_sec // 60; ss = total_sec % 60
        tenths = (elapsed_ms % 1000) // 100
        timer_text = f"{mm:02d}:{ss:02d}.{tenths}"
        draw_timer(screen, timer_text, (settings.SCREEN_WIDTH - 12, 12))

        if game_over:
            font = pygame.font.SysFont(None, 72)
            txt = font.render("GAME OVER", True, (200, 40, 40))
            screen.blit(txt, txt.get_rect(
                center=(settings.SCREEN_WIDTH//2, settings.SCREEN_HEIGHT//3)))

    pygame.display.flip()
    clock.tick(settings.FPS)








