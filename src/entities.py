#entities.py
import pygame
import settings


class Player(pygame.sprite.Sprite):
    def __init__(self, idle_frames, run_frames, x, baseline_y,
                 foot_offset=0, speed=5, anim_fps=12):
        super().__init__()
        self.idle_frames = idle_frames or []
        self.run_frames  = run_frames or []
        self.frame_index = 0

        first_img = (self.idle_frames[0] if self.idle_frames
                     else self.run_frames[0] if self.run_frames
                     else pygame.Surface((1, 1), pygame.SRCALPHA))

        self.image = first_img
        self.rect  = self.image.get_rect()

        self.baseline_y = baseline_y + foot_offset
        self.x = float(x)
        self.y = float(self.baseline_y)
        self.rect.midbottom = (int(self.x), int(self.y))

        self.flip = False
        self.speed = speed
        self.frame_time_ms = 1000 // max(1, anim_fps)
        self._last_update = pygame.time.get_ticks()

        self.vel_y = 0.0
        self.airborne = False
        self.jump_power = settings.JUMP_POWER

    def try_jump(self):
        if not self.airborne:
            self.vel_y = -self.jump_power
            self.airborne = True

    def move_and_animate(self, dx: float):
        self.x += dx
        if dx != 0:
            self.flip = dx < 0

        self.vel_y += settings.GRAVITY
        self.y += self.vel_y
        if self.y >= self.baseline_y:
            self.y = self.baseline_y
            self.vel_y = 0
            self.airborne = False

        seq = self.run_frames if (dx != 0 or self.airborne) else self.idle_frames
        if not seq:
            left = self.rect.left
            self.rect = self.image.get_rect()
            self.rect.left = left
            self.rect.midbottom = (int(self.x), int(self.y))
            return

        now = pygame.time.get_ticks()
        if now - self._last_update >= self.frame_time_ms:
            self._last_update = now
            self.frame_index = (self.frame_index + 1) % len(seq)
        else:
            self.frame_index %= len(seq)

        self.image = seq[self.frame_index]
        left = self.rect.left
        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.midbottom = (int(self.x), int(self.y))

    def draw(self, surf: pygame.Surface):
        surf.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class WolfStatic(pygame.sprite.Sprite):
    def __init__(self, run_frames, idle_img, left_x, baseline_y,
                 foot_offset=0, anim_fps=12, flip=False):
        super().__init__()
        self.frames = run_frames or []
        self.idle_img = idle_img
        self.frame_index = 0

        self.image = self.idle_img if self.idle_img is not None else (
            self.frames[0] if self.frames else pygame.Surface((1, 1), pygame.SRCALPHA)
        )
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
        if not self.running or not self.frames:
            new_img = self.idle_img
            self.frame_index = 0
        else:
            now = pygame.time.get_ticks()
            if now - self._last_update >= self.frame_time_ms:
                self._last_update = now
                self.frame_index = (self.frame_index + 1) % len(self.frames)
            else:
                self.frame_index %= len(self.frames)
            new_img = self.frames[self.frame_index]

        left = self.rect.left
        bottom = self.baseline_y
        self.image = new_img if new_img is not None else self.image
        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.bottom = bottom

    def draw(self, surf: pygame.Surface):
        surf.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class IdleBreather:
    def __init__(self, frames, x, baseline_y, anim_fps=10):
        self.frames = frames or []
        self.index = 0
        self.image = self.frames[0] if self.frames else pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect  = self.image.get_rect()
        self.rect.midbottom = (x, baseline_y)
        self.baseline_y = baseline_y
        self.frame_time_ms = 1000 // max(1, anim_fps)
        self._last = pygame.time.get_ticks()

    def update(self):
        if not self.frames:
            return
        now = pygame.time.get_ticks()
        if now - self._last >= self.frame_time_ms:
            self._last = now
            self.index = (self.index + 1) % len(self.frames)
            left = self.rect.left
            self.image = self.frames[self.index]
            self.rect  = self.image.get_rect()
            self.rect.left = left
            self.rect.bottom = self.baseline_y

    def draw(self, surf: pygame.Surface):
        surf.blit(self.image, self.rect)
