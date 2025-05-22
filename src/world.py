import pygame
import logging

from pygame.sprite import Group

from .region import Region, RegionManager
from .ship import Ship
from .input import Input
from .health import Health


class World:
    __instance = None

    def __init__(self, screen: pygame.Surface, inp: Input):
        self.__logger: logging.Logger = logging.getLogger(__name__)

        self.screen: pygame.Surface = screen
        self.screen_size: tuple[int, int] = self.screen.get_size()

        self.health: Health = Health()
        self.health.reset()

        self.__logger.info("Initializing region manager")
        self.region_manager: RegionManager = self.init_regions(self.screen_size)

        self.__logger.info("Creating sprites groups...")
        self.ship: Ship = Ship(inp)

        self.aliens: Group = Group()
        self.cargoes: Group = Group()
        self.player_bullets: Group = Group()
        self.alien_bullets: Group = Group()
        self.hearts: Group = Group()
        self.shields: Group = Group()
        self.powerups: Group = Group()

    def __new__(cls, *args, **kwargs):
        # To make sure there will be only one world per game
        if not cls.__instance:
            return super(World, cls).__new__(cls)
        raise RuntimeError("Only one instance of World is allowed.")

    def init_regions(self, size: tuple[int, int]) -> RegionManager:
        return RegionManager(size,
            Region("Starfield Stage - 1", "starfield/1.png", 0, size),
            Region("Starfield Stage - 2", "starfield/2.png", 200, size),
            Region("Starfield Stage - 3", "starfield/3.png", 400, size),
            Region("Starfield Stage - 4", "starfield/4.png", 600, size),
            Region("Starfield Stage - 5", "starfield/5.png", 800, size),
            Region("Verdant Expanse Stage - 1", "verdant expanse/1.png", 1100, size),
            Region("Verdant Expanse Stage - 2", "verdant expanse/2.png", 1400, size),
            Region("Verdant Expanse Stage - 3", "verdant expanse/3.png", 1700, size),
            Region("Verdant Expanse Stage - 4", "verdant expanse/4.png", 2000, size),
            Region("Verdant Expanse Stage - 5", "verdant expanse/5.png", 2300, size),
            Region("Violet Void Stage - 1", "violet void/1.png", 2700, size),
            Region("Violet Void Stage - 2", "violet void/2.png", 3100, size),
            Region("Violet Void Stage - 3", "violet void/3.png", 3500, size),
            Region("Violet Void Stage - 4", "violet void/4.png", 3900, size),
            Region("Violet Void Stage - 5", "violet void/5.png", 4300, size)
        )

    def kill_all(self) -> None:
        self.player_bullets.empty()
        self.aliens.empty()
        self.alien_bullets.empty()
        self.cargoes.empty()
        self.hearts.empty()
        self.shields.empty()
        self.powerups.empty()
