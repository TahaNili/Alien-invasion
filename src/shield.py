import secrets
from dataclasses import dataclass

import pygame.image
from pygame import Rect
from pygame.sprite import Sprite

from . import settings


@dataclass
class Shield(Sprite):
    screen: pygame.Surface
    shield_image = pygame.transform.scale(
        pygame.image.load("data/assets/shield/shield.png"),
        (25, 25),
    )

    def __post_init__(self) -> None:
        self.rect: Rect = self.shield_image.get_rect()
        self.rect.centerx = secrets.randbelow(settings.SCREEN_WIDTH + 1)
        self.rect.top = 0

    def update(self):
        self.rect.y += int(settings.HEART_SPEED_FACTOR * settings.DELTA_TIME)

    def draw(self):
        self.screen.blit(self.shield_image, self.rect)
