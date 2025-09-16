## current test file
print("hello")

import pygame

pygame.init()

## Set up a window

screen = pygame.display.set_mode((500,700))
pygame.display.set_caption(" Test")

## Background Fill to white
screen.fill((255,255,255))
pygame.display.flip()

# Main loop to keep the window open and responsive
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


pygame.quit()

print(" is working!")


