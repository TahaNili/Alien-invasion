import pygame
from pygame.sprite import Sprite
from random import randint


class Heart(Sprite):
    """A class to manage generated hearts."""

    def __init__(self, ai_settings, screen):
        super(Heart, self).__init__()
        self.screen = screen

        self.image = pygame.image.load(r'data/assets/hearts/full_heart.png')
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.rect = self.image.get_rect()
        self.screen_rect = screen.get_rect()    
        self.rect.centerx = randint(0, self.screen_rect.right)
        self.rect.top = 0

        # Store the heart's position as a decimal value.
        self.y = 0

        self.speed_factor = ai_settings.heart_speed_factor

    def update(self):
        """Move the heart down the screen."""
        # Update the decimal position of the heart.
        self.y += self.speed_factor

        # Update the rect position
        self.rect.y = self.y

    def draw_heart(self):
        """Draw the heart to the screen."""
        self.screen.blit(self.image, self.rect)
