import pygame
import math
from abc import ABC, abstractmethod
from pygame.sprite import Sprite


class Bullet(ABC, Sprite):
    """An abstract class to create bullets."""

    def __init__(self, ai_settings, screen, target, source, color, speed_factor):
        super(Bullet, self).__init__()
        self.screen = screen

        # Load and scale bullet image
        self.image = pygame.image.load(r'data/assets/sprites/golden_bullet.png')
        self.image_size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.03, self.image_size[1] * 0.03))
        self.rect = self.image.get_rect()

        # Set angle and initial position
        self.angle, self.rect.centerx, self.rect.centery = self.set_angle(source, target)

        # Store the bullet's position as a decimal value
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.color = color
        self.speed_factor = speed_factor

    def update(self):
        """Move the bullet."""
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

    @abstractmethod
    def set_angle(self, source, target):
        """Set the angle and initial position of the bullet."""
        pass


class ShipBullet(Bullet):
    """A class to manage bullets fired from the ship."""

    def __init__(self, ai_settings, screen, ship):
        super().__init__(ai_settings, screen, None, ship, ai_settings.bullet_color, ai_settings.bullet_speed_factor)

    def set_angle(self, source, target):
        angle = source.angle  # Use ship's current angle
        x = source.rect.centerx + math.sin(angle) * 30
        y = source.rect.centery - math.cos(angle) * 30
        return angle, x, y


class AlienBullet(Bullet):
    """A class to manage bullets fired from the aliens."""

    def __init__(self, ai_settings, screen, alien, ship):
        super().__init__(ai_settings, screen, ship, alien, ai_settings.bullet_color, ai_settings.alien_bullet_speed_factor)

    def set_angle(self, source, target):
        dx = target.rect.centerx - source.rect.centerx
        dy = target.rect.centery - source.rect.centery

        angle = math.atan2(-dy, dx) - 90  


        x = source.rect.centerx
        y = source.rect.centery

        return angle, x, y