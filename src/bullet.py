import math
from abc import ABC, abstractmethod

import pygame
from pygame.sprite import Sprite

from src.resources.texture_atlas import TextureAtlas

from . import settings


class Bullet(ABC, Sprite):
    """An abstract class to create bullets."""

    def __init__(self, target, source, color, speed_factor):
        super(Bullet, self).__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()

        # Load and scale bullet image
        self.image: pygame.Surface = TextureAtlas.get_sprite_texture("bullet/golden_bullet.png") # type: ignore
        self.image_size: tuple[int, int] = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.03, self.image_size[1] * 0.03))
        self.rect = self.image.get_rect()

        # Set angle and initial position
        self.angle, self.rect.centerx, self.rect.centery = self.set_angle(source, target) # type: ignore

        # Store the bullet's position as a decimal value
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.color = color
        self.speed_factor = speed_factor

    def update(self):
        """Move the bullet with ship's or alien's angle"""

        # Update the decimal position of the bullet.

        self.x -= math.sin(self.angle) * self.speed_factor * settings.DELTA_TIME
        self.y -= math.cos(self.angle) * self.speed_factor * settings.DELTA_TIME

        # Update the rect position
        self.rect.x = self.x # type: ignore
        self.rect.y = self.y # type: ignore

    def draw(self):
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

    def __init__(self, ship):
        super().__init__(None, ship, settings.BULLET_COLOR, settings.BULLET_SPEED_FACTOR)

    def set_angle(self, source, target): # type: ignore
        angle = source.angle  # Use ship's current angle
        x = source.rect.centerx + math.sin(angle) * 30
        y = source.rect.centery - math.cos(angle) * 30
        return angle, x, y


class AlienBullet(Bullet):
    """A class to manage bullets fired from the aliens."""
    def __init__(self, alien, ship, accuracy: float = 1.0):
        # accuracy: higher => tighter aim; expected around 0.5..2.0
        super().__init__(ship, alien, settings.BULLET_COLOR, settings.BULLET_SPEED_FACTOR)
        self.accuracy = float(accuracy)

    def set_angle(self, source, target): # pyright: ignore[reportIncompatibleMethodOverride]
        dx = target.rect.centerx - source.rect.centerx
        dy = target.rect.centery - source.rect.centery

        # base angle toward target (in radians)
        base_angle = math.atan2(-dy, dx) - math.radians(90)

        # determine accuracy: prefer source.personality then bullet's accuracy
        accuracy = 1.0
        try:
            if hasattr(source, 'personality') and isinstance(source.personality, dict):
                accuracy = float(source.personality.get('accuracy', accuracy))
        except Exception:
            pass
        try:
            accuracy = float(getattr(self, 'accuracy', accuracy))
        except Exception:
            pass

        # compute spread (radians): higher accuracy => smaller spread
        max_spread = 0.6  # tuning constant (radians)
        # avoid division by zero
        acc = max(0.1, accuracy)
        spread = max_spread * (1.0 / acc)

        # use Gaussian noise for natural spread
        try:
            import random
            noisy_angle = base_angle + random.gauss(0, spread)
        except Exception:
            noisy_angle = base_angle

        x = source.rect.centerx
        y = source.rect.centery

        return noisy_angle, x, y
