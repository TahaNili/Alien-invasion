import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
pygame.init()
from src.input import Input
from src.ai_manager import AIManager
from pygame.sprite import Group
from src.game_stats import GameStats
from src.health import Health
from src.settings import Settings

input = Input()

# Minimal fake Ship implementing the necessary interface used by AIManager
class FakeShip:
    def __init__(self):
        self.rect = pygame.Rect(0,0,32,32)
        self.rect.centerx = 400
        self.rect.centery = 500
        self.center = [float(self.rect.centerx), float(self.rect.centery)]
        self.angle = 0.0
        self.moving_left = self.moving_right = self.moving_up = self.moving_down = False

    def update(self):
        # emulate Ship.update angle calculation from input current mouse position
        try:
            mouse_pos = input.current_mouse_position
        except Exception:
            mouse_pos = (0,0)
        dx = mouse_pos[0] - self.center[0]
        dy = mouse_pos[1] - self.center[1]
        import math
        # same calculation as original ship
        self.angle = math.atan2(-dx, -dy)

ship = FakeShip()
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
# emulate ship.update() as the real loop would call after ai.act
ship.update()
print('After act (ship.update run): ship.angle=', ship.angle)
print('bullets:', len(bullets))
pygame.quit()
