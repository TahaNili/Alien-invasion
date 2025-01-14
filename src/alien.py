import pygame
import math
from abc import ABC, abstractmethod
from random import randint
from pygame.sprite import Sprite


class Alien(ABC, Sprite):
    """An abstract class to create aliens."""

    def __init__(self, ai_settings, screen, health):
        """Initialize the alien and set its starting position."""
        super(Alien, self).__init__()

        self.screen = screen
        self.ai_settings = ai_settings
        self.health = health
        self.angle = math.pi

        # Load the alien image and set its rect attribute.
        self.image = self.get_image()
        self.rect = self.image.get_rect()

        # Start each new alien near the top left of the screen.
        self.rect.x = self.rect.width
        self.rect.y = self.rect.height

        # Store the alien's exact position.
        self.x = float(self.rect.x)

    def check_edges(self):
        """Return True if alien is at edge of screen."""
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right:
            return True
        if self.rect.left <= 0:
            return True
        return None

    def update(self):
        """Move the aliens right or left."""
        self.x += (self.ai_settings.alien_speed_factor * self.ai_settings.fleet_direction)
        self.rect.x = self.x

    def bltime(self):
        """Draw the alien at its current location."""
        self.screen.blit(self.image, self.rect)


    @abstractmethod
    def get_image(self):
        pass # This is an abstract method, no implementation here.


class CargoAlien(Alien):
    """A class to represent a single cargo alien in the fleet."""

    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen, ai_settings.alien_l1_health)

        self.rect.x = randint(10, ai_settings.screen_width - 10)
        self.rect.y = self.ai_settings.screen_height + 100

    def update(self):
        self.rect.y -= self.ai_settings.cargo_speed_facto

    def get_image(self):
        image = pygame.image.load(r"data/assets/sprites/alien_cargo.png")
        image_size = image.get_size()
        return pygame.transform.scale(image, (image_size[0] * 0.2, image_size[1] * 0.2))


class AlienL1(Alien):
    """A class to represent a single alien in the fleet."""

    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen, ai_settings.alien_l1_health)

    def get_image(self):
        image = pygame.image.load(r"data/assets/sprites/alien_l1.png")
        return pygame.transform.rotate(image, 180)


class AlienL2(Alien):
    """A class to represent a single alien in the fleet."""

    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen, ai_settings.alien_l2_health)

    def get_image(self):
        image = pygame.image.load(r"data/assets/sprites/alien_l2.png")
        image = pygame.transform.scale(image, (60, 57))
        return pygame.transform.rotate(image, 180)