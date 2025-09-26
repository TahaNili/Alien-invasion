import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
pygame.init()
from pygame.sprite import Group, Sprite

class FakeAlien(Sprite):
    def __init__(self):
        super().__init__()
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.health = 1

class FakeBullet(Sprite):
    def __init__(self):
        super().__init__()
        self.rect = pygame.Rect(0, 0, 4, 8)

aliens = Group()
bullets = Group()

alien = FakeAlien()
alien.rect.centerx = 400
alien.rect.centery = 450
aliens.add(alien)

b = FakeBullet()
b.rect.centerx = 400
b.rect.centery = 450
bullets.add(b)

collisions = pygame.sprite.groupcollide(bullets, aliens, True, False)
print('collisions:', collisions)
print('bullets left:', len(bullets), 'aliens left:', len(aliens))
pygame.quit()
