import secrets

import pygame
from pygame import Rect
from pygame.sprite import Sprite

from . import settings


class Shield(Sprite):
    def __init__(self, screen: pygame.Surface):
        super().__init__()
        self.screen = screen
        self.image = pygame.transform.scale(
            pygame.image.load("data/assets/shield/shield.png"),
            (25, 25),
        )
        self.rect: Rect = self.image.get_rect()
        self.rect.centerx = secrets.randbelow(settings.SCREEN_WIDTH - self.rect.width)
        self.rect.top = 0

    def update(self):
        self.rect.y += int(settings.HEART_SPEED_FACTOR * settings.DELTA_TIME)

    def draw(self):
        self.screen.blit(self.image, self.rect)
