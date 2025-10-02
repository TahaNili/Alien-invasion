import logging
import sys
import pygame
from pygame.sprite import Group
from typing import Any, cast

import src.game_functions as gf
from src.entities.ui.elements.button import Button as btn
from src.entities.ui.elements.difficulty_screen import DifficultyScreen
from src.entities.ui.elements.scoreboard import Scoreboard
from src.recorder import Recorder, collect_frame_features
from src.resources.texture_atlas import TextureAtlas
from src.game_functions import generate_heart
from src.game_stats import GameStats
from src.health import Health
from src.input import Input
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Settings
from src.ship import Ship
from src.log_manager import LogManager
from src.region import Region, RegionManager
from src.difficulty_manager import DifficultyManager
from pathlib import Path


def init_regions(screen: pygame.Surface) -> RegionManager:
    size: tuple[int, int] = screen.get_size()

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

# handle_difficulty_selection will be defined inside run_game so it can access difficulty_screen

def run_game():
    LogManager.init()
    pygame.init()

    logger = logging.getLogger(__name__)

    logger.info("Starting game...")
    logger.info("Initializing game recorder...")
    rec = Recorder()
    csv_path = rec.start_session('gameplay')
    frame_idx = 0

    ai_settings = Settings()
    input = Input()
    difficulty_manager = DifficultyManager()

    screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    TextureAtlas.initialize()
    logger.info("Initializing region manager")
    region_manager: RegionManager = init_regions(screen)

    pygame.display.set_caption("Alien Invasion")

    def handle_difficulty_selection(difficulty: str):
        """Handle difficulty selection and start the game"""
        difficulty_manager.set_preset(difficulty)
        # If selected difficulty uses MLController, ensure models exist
        controller_cls = difficulty_manager.preset.get('controller')
        # check for model files
        models_dir = Path(__file__).parent.parent / 'data' / 'models'
        model_files = list(models_dir.glob('*.joblib')) if models_dir.exists() else []
        # if MLController required and models missing -> show helpful message
        from src.controllers.ml_controller import MLController
        if controller_cls is MLController and not model_files:
            # check if recordings exist
            rec_dir = Path(__file__).parent.parent / 'data' / 'recordings'
            has_recordings = any(rec_dir.glob('*.csv')) if rec_dir.exists() else False
            if has_recordings:
                # models missing but dataset available
                difficulty_screen.show_temporary_message('AI models not found.', 'Run ai_manager.py to train the models (see README.md for details).')
                return
            else:
                # no recordings -> first-time player
                difficulty_screen.show_temporary_message('AI models not found.', 'No recordings found. Play and record sessions or run ai_manager.py to train models.')
                return

        # otherwise proceed to start the game
        gf.run_play_button(ai_settings, stats, ship, aliens, cargoes, bullets, health, region_manager)

    clock = pygame.time.Clock()
    alien_spawn_timer = pygame.time.get_ticks()

    # Create an instance to store game statistics and create scoreboard.
    stats = GameStats()
    sb = Scoreboard(screen, stats)

    health = Health()
    health.reset()

    # Make a ship, and a group for each game sprite.
    ship = Ship(input)
    bullets = Group()
    aliens = Group()
    cargoes = Group()
    alien_bullets = Group()
    hearts = Group()
    shields = Group()

    # Create difficulty selection screen
    difficulty_screen = DifficultyScreen(handle_difficulty_selection)

    def show_difficulty_screen():
        """Show difficulty selection screen instead of starting game directly"""
        difficulty_screen.show()

    play_button = btn(
        "start",
        (240, 64),
        (screen.get_rect().centerx - 120, screen.get_rect().centery + -74),
        show_difficulty_screen,  # Changed to show difficulty screen first
        lambda: not stats.game_active and not stats.credits_active and not difficulty_screen.active,
    )

    credits_button = btn(
        "Credits",
        (240, 64),
        (screen.get_rect().centerx - 120, screen.get_rect().centery + 10),
        lambda: gf.run_credit_button(stats),
        lambda: not stats.credits_active and not stats.game_active,
    )

    back_button = btn(
        "Back",
        (240, 64),
        (10, 50),
        lambda: gf.run_back_button(stats),
        lambda: stats.credits_active,
    )

    alien_spawn_counter = 0

    gf.load_animations(screen)
    gf.load_credits()

    logger.info("Game started")

    # Start the main loop for the game.
    try:
        while True:
            input.update()
            gf.check_events(ai_settings, input, screen, stats, ship, bullets)
            if stats.game_active:
                # Prevent mouse from going out of screen.
                pygame.event.set_grab(True)

                # Update game sprites
                gf.update_game_sprites(
                    ai_settings,
                    screen,
                    stats,
                    sb,
                    ship,
                    aliens,
                    bullets,
                    cargoes,
                    alien_bullets,
                    health,
                    hearts,
                    shields,
                )
            else:
                pygame.event.set_grab(False)
            
            # Update difficulty screen if active
            difficulty_screen.update()

            gf.update_screen(
                region_manager,
                ai_settings,
                screen,
                stats,
                sb,
                ship,
                aliens,
                bullets,
                play_button,
                credits_button,
                back_button,
                cargoes,
                alien_bullets,
                health,
                hearts,
                shields,
            )

            # Record frame data
            features = collect_frame_features(
                ship=ship,
                input_obj=input,
                stats=stats,
                bullets=bullets,
                aliens=aliens,
                cargoes=cargoes,
                alien_bullets=alien_bullets,
                hearts=hearts,
                shields=shields,
                region_manager=region_manager,
            )
            rec.record_frame(frame_idx, clock.get_time(), features)
            frame_idx += 1

            clock.tick(ai_settings.fps)

            # Aliens fire timer
            current_time = pygame.time.get_ticks()

            if region_manager.can_spawn_objects():
                if current_time - alien_spawn_timer > 100:
                    gf.alien_fire(ai_settings, stats, screen, aliens, alien_bullets, ship)

                    generate_heart(stats, screen, hearts)
                    gf.generate_shields(screen, ai_settings, stats, shields)
                    if alien_spawn_counter % 10 == 0:
                        if stats.game_active:
                            # Use difficulty manager to create aliens
                            alien = difficulty_manager.create_alien(
                                lambda: cast(Any, gf.create_alien(ai_settings, screen)))
                            aliens.add(alien)

                    alien_spawn_counter += 1
                    alien_spawn_timer = current_time
            else:
                bullets.empty()
                aliens.empty()
                alien_bullets.empty()
                cargoes.empty()
                hearts.empty()
                shields.empty()

    except Exception:
        # Allow exception to propagate after cleanup
        raise
    finally:
        data_path = rec.stop()
        if data_path:
            print(f"Data has Saved ({data_path})")
        else:
            print("Data NOT saved!")
        pygame.quit()


run_game()