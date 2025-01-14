import pygame
import math
from abc import ABC
from pygame.sprite import Sprite


class Bullet(ABC, Sprite):
    """An abstract class to create bullets."""

    def __init__(self, ai_settings, screen, ship, color, speed_factor):
        super(Bullet, self).__init__()
        self.screen = screen

        # Create a bullet rect (0, 0)
        self.image = pygame.image.load(r'data/assets/sprites/golden_bullet.png')
        self.image_size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.03, self.image_size[1] * 0.03))
        self.rect = self.image.get_rect()

        self.angle = ship.angle
        self.rect.centerx = ship.rect.centerx
        self.rect.top = ship.rect.top

        # Store the bullet's position as a decimal value.
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.color = color
        self.speed_factor = speed_factor

    def update(self):
        """Move the bullet."""
        # Update the decimal position of the bullet.
        self.x -= math.sin(self.angle) * self.speed_factor
        self.y -= math.cos(self.angle) * self.speed_factor

        # Update the rect position
        self.rect.x = self.x
        self.rect.y = self.y

    def draw_bullet(self):
        """Draw the bullet to the screen."""
        rotated_image = pygame.transform.rotate(self.image, math.degrees(self.angle))
        rotated_rec = rotated_image.get_rect(center=(self.rect.centerx, self.rect.centery))
        self.screen.blit(rotated_image, rotated_rec)


class ShipBullet(Bullet):
    """A class to manage bullets fired from the ship."""

    def __init__(self, ai_settings, screen, ship):
        super().__init__(ai_settings, screen, ship, ai_settings.bullet_color, ai_settings.bullet_speed_factor)


class AlienBullet(Bullet):
    """A Class to manage bullets fired from the aliens."""

    def __init__(self, ai_settings, screen, ship):
        super().__init__(ai_settings, screen, ship, ai_settings.bullet_color, ai_settings.alien_bullet_speed_factor)