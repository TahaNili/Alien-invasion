"""Defines the `Shield` class for a falling shield power-up."""

import secrets

import pygame

from src import settings
from src.resources.texture_atlas import TextureAtlas

# Base chance to generate a shield
BASE_SHIELD_CHANCE: int = 60

def get_shield_chance() -> int:
    """Calculate the actual shield spawn chance based on difficulty."""
    preset = settings.DIFFICULTY_PRESETS.get(settings.CURRENT_DIFFICULTY, 
                                           settings.DIFFICULTY_PRESETS["Normal"])
    item_mult = preset.get("item_spawn_mult", 1.0)
    return int(BASE_SHIELD_CHANCE * item_mult)
SHIELD_TIME: int = 10


class Shield(pygame.sprite.Sprite):
    """A shield power-up that spawns randomly and moves downward."""

    def __init__(self) -> None:
        """Initialize the shield with a random position."""
        super().__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()
        img = TextureAtlas.get_sprite_texture("shield/shield.png")
        if img is None:
            raise RuntimeError("Sprite 'shield/shield.png' not found")
        self.image: pygame.Surface = pygame.transform.scale(img, (25, 25))
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.centerx = secrets.randbelow(settings.SCREEN_WIDTH - self.rect.width)
        self.rect.top = 0

    def update(self) -> None:
        """Move the shield downward."""
        self.rect.y += int(settings.HEART_SPEED_FACTOR * settings.DELTA_TIME)

    def draw(self) -> None:
        """Draw the shield on the screen."""
        self.screen.blit(self.image, self.rect)
