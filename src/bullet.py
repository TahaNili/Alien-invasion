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
        self.image: pygame.Surface = TextureAtlas.get_sprite_texture("bullet/golden_bullet.png")
        # Fallback for headless/tests: create a simple surface if atlas not loaded
        if self.image is None:
            try:
                self.image = pygame.Surface((4, 8), pygame.SRCALPHA)
                self.image.fill((255, 255, 0))
            except Exception:
                # Last-resort: create a tiny surface without alpha
                self.image = pygame.Surface((4, 8))
                self.image.fill((255, 255, 0))

        # Safely compute image size and scale (ensure integer sizes >= 1)
        try:
            self.image_size: tuple[int, int] = self.image.get_size()
            target_w = max(1, int(self.image_size[0] * 0.03))
            target_h = max(1, int(self.image_size[1] * 0.03))
            self.image = pygame.transform.scale(self.image, (target_w, target_h))
        except Exception:
            # If scaling fails, keep the original image
            try:
                self.image_size = self.image.get_size()
            except Exception:
                self.image_size = (4, 8)
        self.rect = self.image.get_rect()

        # Set angle and initial position
        self.angle, self.rect.centerx, self.rect.centery = self.set_angle(source, target)

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
        self.rect.x = self.x
        self.rect.y = self.y

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

    def set_angle(self, source, target):
        # Default spawn uses the ship's left gun position (forward + lateral)
        # Forward offset (along ship facing): ~30px. Lateral offset to the
        # left: ~-12px (negative moves left relative to forward direction).
        angle = source.angle
        self.angle = angle  # Use ship's current angle
        forward = 30.0
        lateral_left = (-12.0 if math.sin(self.angle) >= 0 else +12.0)
        # Perpendicular (left) vector components
        perp_x = math.cos(angle + math.pi / 2)
        perp_y = math.sin(angle + math.pi / 2)
        x = source.rect.centerx + math.sin(angle) * forward + perp_x * lateral_left
        y = source.rect.centery - math.cos(angle) * forward + perp_y * lateral_left
        return angle, x, y

    def set_angle_override(self, angle, source_ship):
        """Override bullet angle and position using a ship reference.

        This ensures the bullet's internal angle, rect and float positions are
        consistent and uses the same nose offset logic as `set_angle`.
        """
        try:
            self.angle = float(angle)
            # Use same left-gun math as set_angle
            forward = 30.0
            lateral_left = (-12.0 if math.sin(self.angle) >= 0 else +12.0)
            perp_x = math.cos(self.angle + math.pi / 2)
            perp_y = math.sin(self.angle + math.pi / 2)
            x = source_ship.rect.centerx + math.sin(self.angle) * forward + perp_x * lateral_left
            y = source_ship.rect.centery - math.cos(self.angle) * forward + perp_y * lateral_left
            self.rect.centerx = int(x)
            self.rect.centery = int(y)
            self.x = float(self.rect.x)
            self.y = float(self.rect.y)
        except Exception:
            # If override fails, keep existing values
            pass


class AlienBullet(Bullet):
    """A class to manage bullets fired from the aliens."""

    def __init__(self, alien, ship):
        super().__init__(ship, alien, settings.BULLET_COLOR, settings.BULLET_SPEED_FACTOR)

    def set_angle(self, source, target):
        dx = target.rect.centerx - source.rect.centerx
        dy = target.rect.centery - source.rect.centery

        angle = math.atan2(-dy, dx) - 90

        x = source.rect.centerx
        y = source.rect.centery

        return angle, x, y
