import pygame
from pygame.sprite import Sprite

class AlienBullet(Sprite):
    """A class to manage bullets fired from aliens."""

    def __init__(self, ai_settings, screen, alien):
        """Create a bullet object at the alien's position."""
        super().__init__()
        self.screen = screen

        # Load the bullet image and set its rect
        self.image = pygame.image.load('data/assets/sprites/alien_bullet.png')
        self.image_size = self.image.get_size()
        # Reduce scale factor to make bullets smaller
        scale_factor = 0.015
        self.image = pygame.transform.scale(self.image, (self.image_size[0] * scale_factor, self.image_size[1] * scale_factor))
        self.rect = self.image.get_rect()
        
        # Set the bullet's starting position
        self.rect.centerx = alien.rect.centerx
        self.rect.top = alien.rect.bottom
        
        # Store the bullet's position as a decimal value
        self.y = float(self.rect.y)
        
        # Bullet speed
        self.speed_factor = ai_settings.alien_bullet_speed_factor

    def update(self):
        """Move the bullet down the screen."""
        # Update the decimal position of the bullet
        self.y += self.speed_factor
        
        # Update the rect position
        self.rect.y = self.y

    def draw_bullet(self):
        """Draw the bullet to the screen."""
        self.screen.blit(self.image, self.rect) 