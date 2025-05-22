import pygame
import logging

import src.game_functions as gf

from .log_manager import LogManager
from .input import Input
from .settings import Settings, SCREEN_WIDTH, SCREEN_HEIGHT
from .resources.texture_atlas import TextureAtlas
from .world import World
from .game_stats import GameStats
from .entities.ui.elements.scoreboard import Scoreboard
from .entities.ui.elements.button import Button as btn


class Game:
    def __init__(self):
        LogManager.init()
        pygame.init()

        logger: logging.Logger = logging.getLogger(__name__)

        logger.info("Starting game...")

        logger.info("Initializing settings...")
        self.ai_settings: Settings = Settings()
        self.inp: Input = Input()

        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        logger.info("Initializing texture atlas...")
        TextureAtlas.initialize()

        logger.info("Creating the world...")
        self.world: World = World(self.screen, self.inp)

        pygame.display.set_caption("Alien Invasion")

        self.clock = pygame.time.Clock()

        # Create an instance to store game statistics and create scoreboard.
        self.stats = GameStats()
        self.sb = Scoreboard(self.screen, self.stats)

        gf.load_animations(self.screen)
        gf.load_credits()

        logger.info("Game started")

    def run(self):
        play_button = btn(
            "start",
            (240, 64),
            (self.screen.get_rect().centerx - 120, self.screen.get_rect().centery + -74),
            lambda: gf.run_play_button(self.ai_settings, self.stats, self.world),
            lambda: not self.stats.game_active and not self.stats.credits_active,
        )

        credits_button = btn(
            "Credits",
            (240, 64),
            (self.screen.get_rect().centerx - 120, self.screen.get_rect().centery + 10),
            lambda: gf.run_credit_button(self.stats),
            lambda: not self.stats.credits_active and not self.stats.game_active,
        )

        back_button = btn(
            "Back",
            (240, 64),
            (10, 50),
            lambda: gf.run_back_button(self.stats),
            lambda: self.stats.credits_active,
        )


        alien_spawn_timer = pygame.time.get_ticks()
        alien_spawn_counter = 0

        while True:
            self.inp.update()
            gf.check_events(self.inp, self.stats, self.world)
            if self.stats.game_active:
                # Prevent mouse from going out of screen.
                pygame.event.set_grab(True)

                # Update game sprites
                gf.update_game_sprites(self.ai_settings, self.stats, self.sb, self.world)
            else:
                self.world.ship.reset()
                pygame.event.set_grab(False)

            gf.update_screen(self.ai_settings, self.stats, self.sb, play_button, credits_button, back_button, self.world)

            self.clock.tick(self.ai_settings.fps)

            # Aliens fire timer
            current_time = pygame.time.get_ticks()

            if self.world.region_manager.can_spawn_objects():
                if current_time - alien_spawn_timer > 100:
                    gf.alien_fire(self.ai_settings, self.stats, self.world.aliens, self.world.alien_bullets, self.world.ship)

                    gf.generate_heart(self.stats, self.world)
                    gf.generate_shields(self.stats, self.world.shields)
                    gf.generate_powerup(self.stats, self.world.powerups)

                    if alien_spawn_counter % 10 == 0:
                        gf.spawn_random_alien(self.ai_settings, self.screen, self.world.aliens)

                    alien_spawn_counter += 1
                    alien_spawn_timer = current_time
            else:
                self.world.kill_all()
