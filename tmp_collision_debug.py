import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
pygame.init()
from pygame.sprite import Group, Sprite
from src.settings import Settings

class FakeAlien(Sprite):
    def __init__(self):
        super().__init__()
        self.rect = pygame.Rect(0,0,32,32)
        self.health = 1

class FakeBullet(Sprite):
    def __init__(self):
        super().__init__()
        self.rect = pygame.Rect(0,0,4,8)

aliens = Group(); bullets = Group(); cargoes = Group()
alien = FakeAlien(); alien.rect.centerx=400; alien.rect.centery=450; aliens.add(alien)
b = FakeBullet(); b.rect.centerx=400; b.rect.centery=450; bullets.add(b)

ai_settings = Settings()
print('ai_settings.alien_points', ai_settings.alien_points)

collisions_1 = pygame.sprite.groupcollide(bullets, aliens, True, False)
print('collisions_1:', collisions_1)

# simulate animations placeholder
class DummyAnim:
    def set_position(self,x,y): pass
    def play(self): pass
animations=[DummyAnim(), DummyAnim()]

if collisions_1:
    total_killed = 0
    for aliens_hit in collisions_1.values():
        for alien in aliens_hit:
            print('before health:', alien.health)
            alien.health -= 1
            print('after health:', alien.health)
            animations[0].set_position(alien.rect.x, alien.rect.y)
            animations[0].play()
            if alien.health <= 0:
                try:
                    aliens.remove(alien)
                    total_killed += 1
                    print('removed alien, total_killed now', total_killed)
                except Exception as e:
                    print('remove failed', e)
                    pass

    if total_killed > 0:
        incr = ai_settings.alien_points * total_killed
        print('incrementing score by', incr)
    else:
        print('no total_killed')
else:
    print('no collisions_1')

print('bullets left:', len(bullets), 'aliens left:', len(aliens))
pygame.quit()
