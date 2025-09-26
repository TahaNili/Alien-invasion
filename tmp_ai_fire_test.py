import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pygame
from pygame.sprite import Group

pygame.init()
# create a small screen surface for sprite surfaces
screen = pygame.display.set_mode((800, 600))

from src import game_functions as gf
from src.input import Input
from src.resources.texture_atlas import TextureAtlas

# Create input stub (not used by FakeShip but kept for parity)
inp = Input()
inp._mouse_pos = (400, 300)

# Ensure TextureAtlas returns a Surface even in headless/test setups.
_orig_get = TextureAtlas.get_sprite_texture
def _safe_get(name):
	s = _orig_get(name)
	if s is None:
		# return a small surface placeholder
		return pygame.Surface((8, 8))
	return s

TextureAtlas.get_sprite_texture = staticmethod(_safe_get)

# Use a lightweight fake Ship to avoid loading full ship assets
class FakeShip:
	def __init__(self):
		self.rect = pygame.Rect(0, 0, 32, 32)
		self.center = [400.0, 500.0]
		self.rect.centerx = int(self.center[0])
		self.rect.centery = int(self.center[1])
		self.angle = 0.0
		self.moving_left = self.moving_right = self.moving_up = self.moving_down = False

ship = FakeShip()

bullets = Group()

# 1) Player-style fire (no angle) -> should use ship.angle and spawn at nose (x = centerx + sin(angle)*30)
gf.fire_bullet(ship, bullets)
player_bullet = list(bullets)[-1]
print('player bullet center:', player_bullet.rect.centerx, player_bullet.rect.centery, 'angle:', getattr(player_bullet, 'angle', None))

# advance ticks so debounce won't block next fire
pygame.time.delay(2)

# 2) AI-style fire: pass angle = pi/2 (shoot to the right). This must spawn at ship nose in that direction
import math
ai_angle = math.pi / 2
gf.fire_bullet(ship, bullets, angle=ai_angle)
ai_bullet = list(bullets)[-1]
print('ai bullet center:', ai_bullet.rect.centerx, ai_bullet.rect.centery, 'angle:', getattr(ai_bullet, 'angle', None))

# 3) Direct test: create ShipBullet and call set_angle_override directly
from src.bullet import ShipBullet
sb = ShipBullet(ship)
print('direct created angle before override:', getattr(sb, 'angle', None))
try:
	sb.set_angle_override(ai_angle, ship)
	print('direct after override:', getattr(sb, 'angle', None), 'rect:', sb.rect.center)
except Exception as e:
	print('override raised', e)

pygame.quit()
print('done')

# 4) AI sets ship.angle and fires without angle override (player contract)
import math as _math
pygame.init()
ship.angle = _math.pi / 4
# advance ticks again
pygame.time.delay(2)
gf.fire_bullet(ship, bullets)
ai_via_ship = list(bullets)[-1]
print('ai-via-ship bullet center:', ai_via_ship.rect.centerx, ai_via_ship.rect.centery, 'angle:', getattr(ai_via_ship, 'angle', None))

pygame.quit()
print('done-ai-via-ship')
