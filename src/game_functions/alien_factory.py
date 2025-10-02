"""
Functions for creating and spawning aliens
"""
from random import randint
from typing import Protocol
import pygame
from src.alien import AlienL1, AlienL2

class AlienProtocol(Protocol):
    controller: 'property'

def create_alien(ai_settings, screen) -> AlienProtocol:
    """Create a random alien (L1 or L2) based on spawn chance"""
    if randint(1, 100) <= ai_settings.alien_l2_spawn_chance:
        alien = AlienL2(ai_settings, screen)
        alien.health = ai_settings.alien_l2_health
    else:
        alien = AlienL1(ai_settings, screen)
        alien.health = ai_settings.alien_l1_health
    return alien