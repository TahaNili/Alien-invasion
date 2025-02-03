import pygame.image
from pygame.sprite import Sprite
from random import randint


class Shield(Sprite):
    def __init__(self, ai_settings, screen):
        super(Shield, self).__init__()

        self.ai_settings = ai_settings
        self.screen = screen
        self.shield_image = pygame.image.load("data/assets/shield/shield.png")
        self.shield_image = pygame.transform.scale(self.shield_image, (25, 25))
        self.rect = self.shield_image.get_rect()
        self.rect.centerx = randint(0, self.ai_settings.screen_width)
        self.rect.top = 0

        # Store the heart's position as a decimal value.
        self.y = 0

        self.speed_factor = self.ai_settings.heart_speed_factor

    def update(self):
        self.y += self.speed_factor * self.ai_settings.delta_time
        self.rect.y = self.y

    def draw(self):
        self.screen.blit(self.shield_image, self.rect)
