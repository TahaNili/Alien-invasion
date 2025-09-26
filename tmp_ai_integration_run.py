import os
os.environ['SDL_VIDEODRIVER']='dummy'
import pygame
pygame.init()
from src.input import Input
from src.ai_manager import AIManager
from src.ship import Ship
from src.game_stats import GameStats
from src.health import Health
from src.settings import Settings
from pygame.sprite import Group
import src.game_functions as gf

input = Input()
settings = Settings()
stats = GameStats()
stats.game_active = True
health = Health(); health.reset()
screen = pygame.display.set_mode((800,600))
# Use a FakeShip to avoid loading textures in headless test
class FakeShip:
    def __init__(self, input):
        self.input = input
        self.rect = pygame.Rect(0,0,32,32)
        self.rect.centerx = 400
        self.rect.centery = 500
        self.center = [float(self.rect.centerx), float(self.rect.centery)]
        self.angle = 0.0
        self.moving_left = self.moving_right = self.moving_up = self.moving_down = False
    def update(self):
        try:
            mx, my = self.input.current_mouse_position
        except Exception:
            mx, my = (0,0)
        dx = mx - self.center[0]
        dy = my - self.center[1]
        import math
        self.angle = math.atan2(-dx, -dy)

ship = FakeShip(input)
aliens = Group(); bullets = Group(); cargoes = Group(); alien_bullets = Group(); hearts = Group(); shields = Group()

ai = AIManager(models_dir='models', trainer_cmd=None)
ai.set_enabled(True)

# add target alien
from pygame.sprite import Sprite
class FakeAlien(Sprite):
    def __init__(self):
        super().__init__()
        self.rect = pygame.Rect(0,0,32,32)
        self.rect.centerx = ship.rect.centerx
        self.rect.centery = ship.rect.centery - 120
        self.health = 1
        self.ai_settings = settings
aliens.add(FakeAlien())

# emulate one frame of the main loop (new ordering)
input.update()
ai.act(stats, ship, aliens, bullets, health, input, alien_bullets=alien_bullets, cargoes=cargoes, shields=shields, hearts=hearts)
# Now call check_mouse_events which should see the simulated mouse press
gf.check_mouse_events(settings, input, screen, stats, ship, bullets)
# Update ship and bullets
gf.update_game_sprites(settings, screen, stats, None, ship, aliens, bullets, cargoes, alien_bullets, health, hearts, shields)
print('bullets after frame:', len(bullets))
pygame.quit()
