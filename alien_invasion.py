import logging
import pygame
from pygame.sprite import Group

import src.game_functions as gf
from src.entities.ui.elements.button import Button as btn
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
from src.recorder import Recorder
from src.ai_manager_combined import AIManager
# NOTE: legacy implementations preserved in `src/ai_manager.py` and `src/ai_manager_new.py`.


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

    ai_settings = Settings()
    input = Input()

    # AI manager: will auto-train in background and provide predictions/acts
    ai_manager = AIManager(models_dir="models", trainer_cmd=["python", "tools/train_imitation.py"], auto_train_interval=120)
    ai_manager._idle_frames = 0
    import atexit
    atexit.register(lambda: ai_manager.stop())

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

    play_button = btn(
        "start",
        (240, 64),
        (screen.get_rect().centerx - 120, screen.get_rect().centery + -74),
        lambda: gf.run_play_button(ai_settings, stats, ship, aliens, cargoes, bullets, health, region_manager),
        lambda: not stats.game_active and not stats.credits_active,
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

    # Initialize recorder (will create data/gameplay_log.csv)
    try:
        recorder = Recorder("data/gameplay_log.csv")
        logger.info("Recorder initialized")
    except Exception:
        recorder = None
        logger.exception("Failed to initialize Recorder")

    # Start the main loop for the game.
    idle_timeout_seconds = 2.0
    last_active_time = pygame.time.get_ticks()
    while True:
        input.update()

        # Handle AI toggle key (K) immediately after input.update() so a
        # user's explicit toggle is detected before any AI may overwrite
        # input state for this frame. This mirrors the previous AI's
        # behavior where user input had priority.
        try:
            if input.is_key_pressed(pygame.K_k):
                # user explicitly toggles AI (mark as user-controlled)
                ai_manager.set_enabled(not ai_manager.ai_enabled, auto=False)
        except Exception:
            pass

        # If AI enabled, and the user performed ANY action this frame
        # (pressing keys, mouse button, or moving the mouse), we should
        # immediately disable AI so the player regains control. This
        # matches the legacy behaviour requested: any user activity
        # disables AI when it was active.
        try:
            if ai_manager.ai_enabled:
                user_did_action = False

                # Key presses (any key pressed this frame)
                # We check is_key_pressed across a small set of relevant keys
                # plus a general technique: attempt to detect any change in
                # the key state tuples sizes safely.
                # Specific control keys used in gameplay:
                for k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_z, pygame.K_x):
                    try:
                        if input.is_key_pressed(k):
                            user_did_action = True
                            break
                    except Exception:
                        continue

                # Mouse presses
                if not user_did_action:
                    try:
                        if input.is_mouse_button_pressed(0) or input.is_mouse_button_pressed(1) or input.is_mouse_button_pressed(2):
                            user_did_action = True
                    except Exception:
                        pass

                # Mouse movement (cursor moved since last frame)
                if not user_did_action:
                    try:
                        if input.get_mouse_cursor_position() != input.previous_mouse_position:
                            user_did_action = True
                    except Exception:
                        pass

                # If user did something, disable AI (treat as user-controlled)
                if user_did_action:
                    ai_manager.set_enabled(False, auto=False)
        except Exception:
            pass

        # If AI enabled, let AI decide movement/actions BEFORE input handlers
        # so simulated mouse/keyboard state will be visible to the same
        # frame's input-processing (check_events / check_mouse_events).
        if ai_manager.ai_enabled:
            try:
                ai_manager.act(
                    stats,
                    ship,
                    aliens,
                    bullets,
                    health,
                    input,
                    alien_bullets=alien_bullets,
                    items=None,
                    cargoes=cargoes,
                    shields=shields,
                    hearts=hearts,
                )
            except Exception:
                pass

        # Record current frame only when game is active (best-effort)
        try:
            if recorder is not None and stats.game_active:
                recorder.record(stats, ship, aliens, bullets, health, input)
        except Exception:
            # Never let recorder break the game loop
            logger.exception("Recorder failed during record()")

        # (AI toggle handled earlier immediately after input.update())

        # detect inactivity using time (2 seconds) -> enable AI control
        try:
            user_active = (
                input.is_key_down(pygame.K_LEFT)
                or input.is_key_down(pygame.K_RIGHT)
                or input.is_key_down(pygame.K_UP)
                or input.is_key_down(pygame.K_DOWN)
                or input.is_mouse_button_down(0)
            )
        except Exception:
            user_active = True

        now = pygame.time.get_ticks()
        if user_active:
            last_active_time = now
            # if user interacts, immediately disable AI if it was auto-enabled
            try:
                if ai_manager.ai_enabled and ai_manager.was_auto_enabled():
                    ai_manager.set_enabled(False, auto=False)
            except Exception:
                pass
        else:
            # user inactive; if idle timeout exceeded, enable AI
            if (now - last_active_time) >= int(idle_timeout_seconds * 1000):
                # auto-enable AI due to inactivity
                ai_manager.set_enabled(True, auto=True)
        gf.check_events(ai_settings, input, screen, stats, ship, bullets)
        if stats.game_active:
            # Prevent mouse from going out of screen.
            pygame.event.set_grab(True)

            # If AI enabled, let AI decide movement/actions BEFORE sprite updates
            if ai_manager.ai_enabled:
                try:
                    ai_manager.act(
                        stats,
                        ship,
                        aliens,
                        bullets,
                        health,
                        input,
                        alien_bullets=alien_bullets,
                        items=None,
                        cargoes=cargoes,
                        shields=shields,
                        hearts=hearts,
                    )
                except Exception:
                    pass

            # Update game sprites (ship.update will read movement flags set by AI)
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

        # Draw AI status at bottom-left
        try:
            from src import settings as _settings
            font = _settings.FONT
            status_text = f"AI: {'ON' if ai_manager.ai_enabled else 'OFF'}"
            surf = font.render(status_text, True, (255, 255, 255))
            screen.blit(surf, (10, screen.get_height() - surf.get_height() - 10))
            pygame.display.update()
        except Exception:
            pass

        clock.tick(ai_settings.fps)

        # Aliens fire timer
        current_time = pygame.time.get_ticks()

        if region_manager.can_spawn_objects():
            if current_time - alien_spawn_timer > 100:
                gf.alien_fire(ai_settings, stats, screen, aliens, alien_bullets, ship)

                generate_heart(stats, screen, hearts)
                gf.generate_shields(screen, ai_settings, stats, shields)

                if alien_spawn_counter % 10 == 0:
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


run_game()

import logging
import pygame
from pygame.sprite import Group

import src.game_functions as gf
from src.entities.ui.elements.button import Button as btn
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

    ai_settings = Settings()
    input = Input()

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

    play_button = btn(
        "start",
        (240, 64),
        (screen.get_rect().centerx - 120, screen.get_rect().centery + -74),
        lambda: gf.run_play_button(ai_settings, stats, ship, aliens, cargoes, bullets, health, region_manager),
        lambda: not stats.game_active and not stats.credits_active,
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

        clock.tick(ai_settings.fps)

        # Aliens fire timer
        current_time = pygame.time.get_ticks()

        if region_manager.can_spawn_objects():
            if current_time - alien_spawn_timer > 100:
                gf.alien_fire(ai_settings, stats, screen, aliens, alien_bullets, ship)

                generate_heart(stats, screen, hearts)
                gf.generate_shields(screen, ai_settings, stats, shields)

                if alien_spawn_counter % 10 == 0:
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


run_game()
