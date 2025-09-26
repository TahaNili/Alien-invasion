import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
pygame.init()
from src.ship import Ship
from src.input import Input
from src.ai_manager import AIManager
from pygame.sprite import Group
from src.game_stats import GameStats
from src.health import Health
from src.settings import Settings

input = Input()
ship = Ship(input)
aliens = Group()
bullets = Group()
health = Health(); health.reset()
stats = GameStats()
ai_settings = Settings()

ai = AIManager(models_dir='models', trainer_cmd=None)
ai.set_enabled(True)

# Create a fake alien target so AI has something to shoot at
from pygame.sprite import Sprite
class FakeAlien(Sprite):
    def __init__(self):
        super().__init__()
        self.rect = pygame.Rect(0,0,32,32)
        self.rect.centerx = ship.rect.centerx
        self.rect.centery = ship.rect.centery - 120
        self.health = 1
        self.ai_settings = ai_settings

aliens.add(FakeAlien())

print('Before act: ship.angle=', ship.angle)
ai.act(stats, ship, aliens, bullets, health, input, alien_bullets=None, items=None, cargoes=None, shields=None, hearts=None)
print('After act: ship.angle=', ship.angle)
print('bullets:', len(bullets))
pygame.quit()
