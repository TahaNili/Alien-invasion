import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
pygame.init()
from pygame.sprite import Group
from src.input import Input
from src import game_functions as gf
from src.settings import Settings
import pygame

# minimal setup
screen = pygame.display.set_mode((800,600))
ai_settings = Settings()
input = Input()

# Fake ship to avoid asset loading
class FakeShip:
	def __init__(self):
		self.rect = pygame.Rect(0,0,32,32)
		self.center = [400.0, 500.0]
		self.rect.centerx = 400
		self.rect.centery = 500

ship = FakeShip()

aliens = Group()
bullets = Group()
from pygame.sprite import Sprite

# Fake alien simple sprite
class FakeAlien(Sprite):
	def __init__(self):
		super().__init__()
		self.rect = pygame.Rect(0,0,32,32)
		self.health = 1

alien = FakeAlien()
alien.rect.centerx = 400
alien.rect.centery = 450
aliens.add(alien)

# Create a bullet that will collide
from pygame.sprite import Sprite

# Fake bullet sprite
class FakeBullet(Sprite):
	def __init__(self):
		super().__init__()
		self.rect = pygame.Rect(0,0,4,8)

b = FakeBullet()
b.rect.centerx = 400
b.rect.centery = 450
bullets.add(b)

# scoreboard
from src.game_stats import GameStats
from src.entities.ui.elements.scoreboard import Scoreboard
stats = GameStats()
sb = Scoreboard(screen, stats)
from pygame.sprite import Group

# Run collision check with empty cargoes and dummy animations
cargoes = Group()
class DummyAnim:
	def set_position(self, x, y):
		pass
	def play(self):
		pass
animations = [DummyAnim(), DummyAnim()]
gf.check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes, animations)
print('score after collision:', stats.score)
pygame.quit()
print('done')
