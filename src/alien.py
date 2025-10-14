import pygame
import math
from abc import ABC, abstractmethod
from random import randint
from pygame.sprite import Sprite

from src.resources.texture_atlas import TextureAtlas


from src.protocols import AlienProtocol, ControllerProtocol

class Alien(ABC, Sprite, AlienProtocol):
    """An abstract class to create aliens."""

    def __init__(self, ai_settings, screen):
        """Initialize the alien and set its starting position."""
        super(Alien, self).__init__()

        self.screen = screen
        self.ai_settings = ai_settings
        self.health = 1  # Default health
        self.angle = 0
        self._controller: ControllerProtocol | None = None  # Will be set by DifficultyManager
        self.has_shield = False
        self.shield_time = 0
        self.shield_duration = 10000  # 10 seconds in milliseconds
        # Load the alien image and set its rect attribute.
        self.original_image = self.get_image()
        self.image = self.original_image
        self.rect = self.image.get_rect()

        # Default starting position (can be overridden by spawn functions)
        self.x = float(randint(0, max(1, self.ai_settings.screen_width - self.rect.width)))
        self.y = float(randint(0, max(1, self.ai_settings.screen_height - self.rect.height)))
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
    @property
    def controller(self) -> ControllerProtocol:
        """Get the alien's controller"""
        if self._controller is None:
            from src.controllers.default_controller import DefaultController
            self._controller = DefaultController(self, {})
        return self._controller
        
    @controller.setter
    def controller(self, value: ControllerProtocol):
        """Set the alien's controller"""
        self._controller = value

    def check_edges(self):
        """Return True if alien is at edge of screen."""
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right:
            return True
        if self.rect.left <= 0:
            return True
        return None

    def update(self, ship):
        """Move the alien."""

        # Calculate the distance between the alien and the ship.
        delta_x = ship.rect.centerx - self.rect.centerx
        delta_y = ship.rect.centery - self.rect.centery

        # Calculate the target angle of movement.
        target_angle = math.atan2(delta_y, delta_x)
        target_angle_deg = -math.degrees(target_angle)

        # Smoothly adjust the angle.
        angle_diff = (target_angle_deg - self.angle) % 360
        if angle_diff > 180:
            angle_diff -= 360
        self.angle += angle_diff * 0.1  # Adjust this factor for smoother rotation.

        # Update the alien's position.
        self.x += math.cos(target_angle) * self.ai_settings.alien_speed_factor * self.ai_settings.delta_time
        self.y += math.sin(target_angle) * self.ai_settings.alien_speed_factor * self.ai_settings.delta_time
        self.rect.x = self.x
        self.rect.y = self.y

        # Rotate the alien to face the ship.
        self.image = pygame.transform.rotate(self.original_image, self.angle + 90)

        # Keep the alien within the screen bounds.
        screen_rect = self.screen.get_rect()
        self.rect.clamp_ip(screen_rect)

    def blit(self):
        """Draw the alien at its current location."""
        self.screen.blit(self.image, self.rect)

    @abstractmethod
    def get_image(self):
        """Return the alien's image."""
        image = TextureAtlas.get_sprite_texture("alien/alien_default.png")
        if image is None:
            raise RuntimeError("Sprite 'alien/alien_default.png' not found")
        return pygame.transform.rotate(image, 180)


class CargoAlien(Alien):
    """A class to represent a single cargo alien."""

    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen)
        self.health = ai_settings.alien_l1_health  # Use L1 health for cargo aliens
        self.rect.x = randint(10, ai_settings.screen_width - 10)
        self.rect.y = self.ai_settings.screen_height + 100

    def update(self, ship):
        super().update(ship)
        # Update shield timer if shield is active
        if self.has_shield:
            self.shield_time -= self.ai_settings.delta_time
            if self.shield_time <= 0:
                self.has_shield = False
            
    def collide_with_player(self, player) -> bool:
        """Handle collision with player"""
        if self.has_shield:
            # If both have shields, both survive but shields are consumed
            if player.has_shield:
                self.has_shield = False
                return False
            else:
                # Player takes damage if they don't have a shield
                player.health -= 1
                self.has_shield = False
                return True
        return False
        
    def get_image(self):
        image = TextureAtlas.get_sprite_texture("alien/alien_cargo.png")
        if image is None:
            raise RuntimeError("Sprite 'alien/alien_cargo.png' not found")
        image_size = image.get_size()
        new_size = (int(image_size[0] * 0.2), int(image_size[1] * 0.2))
        return pygame.transform.scale(image, new_size)


class AlienL1(Alien):
    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen)
        self.health = ai_settings.alien_l1_health

    def get_image(self):
        image = TextureAtlas.get_sprite_texture("alien/alien_l1.png")
        if image is None:
            raise RuntimeError("Sprite 'alien/alien_l1.png' not found")
        return pygame.transform.rotate(image, 180)

class AlienL2(Alien):
    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen)
        self.health = ai_settings.alien_l2_health

    def get_image(self):
        image = TextureAtlas.get_sprite_texture("alien/alien_l2.png")
        if image is None:
            raise RuntimeError("Sprite 'alien/alien_l2.png' not found")
        image = pygame.transform.scale(image, (60, 57))
        return pygame.transform.rotate(image, 180)
