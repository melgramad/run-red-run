import sys
from pathlib import Path
import pygame

pygame.init()


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
LOGO = ASSETS / "standing.png"

if not LOGO.is_file():
    raise FileNotFoundError(f"Missing asset: {LOGO} (does it exist and match case?)")

# Set up a window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Run Red, Run!")

class Character(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(str(LOGO)).convert_alpha()
        self.image = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
        self.rect = self.image.get_rect()#Controlling positions and collisions
        self.rect.center = (x, y)

    def draw(self):
         screen.blit(self.image, self.rect)
    


player = Character(200,200, 1)


        
x = 200
y = 200
scale = 1



# Main loop to keep the window open and responsive
run = True
while run:

    screen.fill((30,30,30))
    player.draw()
    pygame.display.flip()
    
   

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()



pygame.quit()







