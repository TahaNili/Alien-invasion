import logging
import pygame
from pathlib import Path
from pygame.sprite import Group

import src.game_functions as gf
from src.entities.ui.elements.button import Button as btn
from src.entities.ui.elements.difficulty_screen import DifficultyScreen
from src.entities.ui.elements.scoreboard import Scoreboard
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
from src.ai_manager import AIManager
from src.item_agent import on_pickup, should_pickup
from src.controllers.ml_controller import MLController
from src.recorder import Recorder, collect_frame_features


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

def run_game():
    LogManager.init()
    pygame.init()

    logger = logging.getLogger(__name__)
    logger.info("Starting game...")
    
    # Initialize AI Manager for ML controllers
    ai_manager = AIManager()
    logger.info("AI Manager initialized")

    ai_settings = Settings()
    input = Input()
    difficulty_manager = DifficultyManager()

    screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    TextureAtlas.initialize()
    logger.info("Initializing region manager")
    region_manager: RegionManager = init_regions(screen)

    pygame.display.set_caption("Alien Invasion")

    clock = pygame.time.Clock()
    alien_spawn_timer = pygame.time.get_ticks()

    # Create an instance to store game statistics and create scoreboard.
    stats = GameStats()
    sb = Scoreboard(screen, stats)

    # Recorder: we will start/stop sessions when gameplay starts/stops
    recorder = Recorder()
    recording_active = False

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

    def handle_difficulty_selection(difficulty: str):
        """Handle difficulty selection and start the game"""
        difficulty_manager.set_preset(difficulty)
        # For this project, any difficulty other than 'Easy' requires trained ML models.
        # If models are missing, block starting the selected difficulty and inform the user.
        if str(difficulty).lower() != 'easy':
            models_dir = getattr(ai_manager, 'models_dir', Path('data/models'))
            model_files = list(models_dir.glob('*.joblib')) if models_dir.exists() else []
            if not model_files:
                msg = (
                    f"AI models not found in {models_dir}. "
                    "Please run: python -m src.ai_manager --train to create models before starting this difficulty."
                )
                logger.warning(msg)
                try:
                    print(msg)
                except Exception:
                    pass
                difficulty_screen.show_temporary_message(
                    'AI models not found.',
                    'Run ai_manager.py to train models (see README)'
                )
                return
        # Start the game with selected difficulty
        gf.run_play_button(ai_settings, stats, ship, aliens, cargoes, bullets, health, region_manager)
        
    # Create difficulty screen
    # Background trainer: runs ai_manager.train in a separate thread and reports status
    import threading
    import subprocess

    def start_background_training():
        def _train():
            try:
                difficulty_screen.set_training_active(True)
                difficulty_screen.show_temporary_message(None, 'Training started...', 3000)
                # Run ai_manager in a subprocess to isolate from game process
                cmd = ["python", "-m", "src.ai_manager", "--train"]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                out, err = proc.communicate()
                if proc.returncode == 0:
                    difficulty_screen.show_temporary_message(None, 'Training completed', 4000)
                    logger.info('AI training finished successfully')
                else:
                    difficulty_screen.show_temporary_message('Training failed', None, 4000)
                    logger.warning('AI training failed: %s', err)
            except Exception as e:
                difficulty_screen.show_temporary_message('Training error', None, 4000)
                logger.exception('Error running background training: %s', e)
            finally:
                try:
                    difficulty_screen.clear_training_active()
                except Exception:
                    pass
        t = threading.Thread(target=_train, daemon=True)
        t.start()

    difficulty_screen = DifficultyScreen(handle_difficulty_selection, on_train=start_background_training)
    
    play_button = btn(
        "START",
        (240, 64),
        (screen.get_rect().centerx - 120, screen.get_rect().centery + -74),
        difficulty_screen.show,  # Show difficulty screen instead of starting directly
        lambda: not stats.game_active and not stats.credits_active and not difficulty_screen.active,
    )

    credits_button = btn(
        "Credits",
        (240, 64),
        (screen.get_rect().centerx - 120, screen.get_rect().centery + 10),
        lambda: gf.run_credit_button(stats),
        lambda: not stats.credits_active and not stats.game_active and not difficulty_screen.active,
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
    while True:
        # Handle input first
        input.update()
        
        # Clear screen at start of frame
        screen.fill((0, 0, 0))
        
        # Always check events, but let difficulty screen handle them when active
        gf.check_events(ai_settings, input, screen, stats, ship, bullets, difficulty_screen)
        
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
            # If recorder not active, start a session named by difficulty
            if not recording_active:
                # Use the DifficultyManager.preset_name (fallback to 'Easy')
                preset = getattr(difficulty_manager, 'preset_name', 'Easy') or 'Easy'
                try:
                    recorder.start_session(f"gameplay_{preset}")
                    recording_active = True
                except Exception as e:
                    print(f"Failed to start recorder: {e}")
            # Record a single frame's features
            try:
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
                # dt in seconds
                recorder.record_frame(pygame.time.get_ticks(), clock.get_time() / 1000.0, features)
            except Exception:
                pass
        else:
            pygame.event.set_grab(False)

        # Draw main game UI first
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
        
        # Draw difficulty screen with semi-transparent overlay when active
        # Let the difficulty screen handle its own drawing when active
        if difficulty_screen.active:
            difficulty_screen.update()
        
        # Update display at end of frame
        pygame.display.flip()
        
        clock.tick(ai_settings.fps)

        # Aliens fire timer
        current_time = pygame.time.get_ticks()

        if region_manager.can_spawn_objects():
            # Calculate spawn interval based on difficulty
            spawn_multiplier = difficulty_manager.preset.get("spawn_multiplier", 1.0)
            adjusted_interval = ai_settings.base_spawn_interval / spawn_multiplier
            
            if current_time - alien_spawn_timer > adjusted_interval:
                gf.alien_fire(ai_settings, stats, screen, aliens, alien_bullets, ship)
                
                generate_heart(stats, screen, hearts)
                gf.generate_shields(screen, ai_settings, stats, shields)
                
                # Spawn aliens more frequently based on spawn_multiplier
                spawn_frequency = max(1, int(10 / spawn_multiplier))
                if alien_spawn_counter % spawn_frequency == 0:
                    gf.spawn_random_alien(ai_settings, screen, aliens)
                
                alien_spawn_counter += 1
                alien_spawn_timer = current_time
        else:
            bullets.empty()
            aliens.empty()
            alien_bullets.empty()
            cargoes.empty()
            hearts.empty()
            shields.empty()

        # If the game is not active and recording was active, stop and save
        if not stats.game_active and recording_active:
            try:
                path = recorder.stop()
                if path:
                    print(f"Recording stopped and saved to: {path}")
            except Exception as e:
                print(f"Error stopping recorder: {e}")
            recording_active = False


run_game()