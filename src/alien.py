import pygame
from pygame.sprite import Sprite
import random
from src.alien_bullet import AlienBullet


class Alien(Sprite):
    """A class to represent a single alien in the fleet."""

    def __init__(self, ai_settings, screen, type=0):
        """Initialize the alien and set its starting position."""
        super().__init__()
        self.screen = screen
        self.ai_settings = ai_settings
        self.type = type
        
        # Load the alien image and set its rect attribute
        if self.type == 0:  # Normal alien
            self.image = pygame.image.load(r'data/assets/sprites/alien_l1.png')
        elif self.type == 1:  # Cargo ship
            self.image = pygame.image.load(r'data/assets/sprites/alien_cargo.png')
        
        self.rect = self.image.get_rect()
        
        # Start each new alien near the top left of the screen
        self.rect.x = self.rect.width
        self.rect.y = self.rect.height
        
        # Store the alien's exact position
        self.x = float(self.rect.x)
        
        # Shooting cooldown
        self.shoot_cooldown = 0
        self.shoot_delay = random.randint(60, 180)  # Random delay between shots

    def check_edges(self):
        """Return True if alien is at edge of screen."""
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right:
            return True
        elif self.rect.left <= 0:
            return True
        
    def update(self, alien_bullets=None):
        """Move the alien right or left."""
        self.x += (self.ai_settings.alien_speed_factor * 
                    self.ai_settings.fleet_direction)
        self.rect.x = self.x
        
        # Update shooting cooldown and try to shoot only for normal aliens
        if self.type == 0:  # Normal alien
            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1
            
            # Try to shoot if cooldown is 0 and we have alien_bullets group
            if alien_bullets is not None and self.shoot_cooldown <= 0:
                self.try_shoot(alien_bullets)

    def try_shoot(self, alien_bullets):
        """Try to shoot a bullet."""
        if len(alien_bullets) < self.ai_settings.alien_bullets_allowed:
            if random.random() < self.ai_settings.alien_shoot_chance:
                new_bullet = AlienBullet(self.ai_settings, self.screen, self)
                alien_bullets.add(new_bullet)
                self.shoot_cooldown = self.shoot_delay

    def bltime(self):
        """Draw the alien at its current location."""
        self.screen.blit(self.image, self.rect)
