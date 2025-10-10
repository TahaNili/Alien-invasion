"""
Game Functions Module
===================

This module contains all the core game functionality for Alien Invasion.
It handles:
- Sprite creation and management (aliens, bullets, items)
- Game events and input processing
- Collision detection and response
- Screen updates and rendering
- Debug and development tools

The functions are organized into logical sections for better readability
and maintenance.
"""

import sys
import logging
from random import choice, randint
from time import sleep
from typing import Optional, List, Tuple, Any, Protocol, Type

import pygame
from pygame.sprite import Group, Sprite

from src.alien import AlienL1, AlienL2, CargoAlien, AlienProtocol
from src.settings import Settings as AISettings
from src.animation import Animation
from src.bullet import AlienBullet, ShipBullet
from src.entities.items.heart import GENERATE_HEART_CHANCE, Heart
from src.entities.items.shield import GENERATE_SHIELD_CHANCE, Shield
from src.item_agent import should_pickup, on_pickup
from src.protocols import AlienProtocol

from . import settings
from .game_stats import GameStats
from .resources.texture_atlas import TextureAtlas

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# Sound Effects
# ------------
sound_fire = pygame.mixer.Sound(settings.SOUNDS_DIR / "fire.ogg")
sound_explosion = pygame.mixer.Sound(settings.SOUNDS_DIR / "explosion.ogg")
sound_life = pygame.mixer.Sound(settings.SOUNDS_DIR / "life_pickup.flac")
sound_damage = pygame.mixer.Sound(settings.SOUNDS_DIR / "damage.wav")
sound_shield_fill = pygame.mixer.Sound(settings.SOUNDS_DIR / "shield_fill.wav")
sound_shield_empty = pygame.mixer.Sound(settings.SOUNDS_DIR / "shield_empty.wav")

# Global State
# -----------
text_lines: List[pygame.Surface] = []  # Rendered text surfaces for credits
text_rects: List[pygame.Rect] = []     # Positioning rectangles for credit text
animations: List[Animation] = []        # Active animations
spawn_points: List[Tuple[int, int, int]] = []  # Recent spawn points for debug overlay
DEBUG_OVERLAY: bool = False  # Toggle for debug visualization

def toggle_debug_overlay():
    """Toggle the debug overlay display."""
    global DEBUG_OVERLAY
    DEBUG_OVERLAY = not DEBUG_OVERLAY

def draw_debug_overlay(screen):
    """Draw debug information including recent spawn points."""
    if not DEBUG_OVERLAY:
        return
        
    # Draw recent spawn points
    for point in spawn_points[-10:]:  # Keep only last 10 spawn points
        pygame.draw.circle(screen, (255, 0, 0), point, 5)
        
    # Clean up old spawn points after 5 seconds
    current_time = pygame.time.get_ticks()
    spawn_points[:] = [p for p in spawn_points if current_time - p[2] < 5000]

# Alien Creation and Spawning
# -------------------------

def determine_alien_type(ai_settings: AISettings) -> Type[AlienL1] | Type[AlienL2]:
    """
    Determine which type of alien to spawn based on game settings.
    
    Args:
        ai_settings: Game settings containing alien spawn configuration
        
    Returns:
        Union[Type[AlienL1], Type[AlienL2]]: The concrete alien class to instantiate
    """
    return AlienL2 if randint(1, 100) <= ai_settings.alien_l2_spawn_chance else AlienL1

def set_alien_health(alien: AlienProtocol, ai_settings: AISettings) -> None:
    """
    Configure the health for a newly created alien.
    
    Args:
        alien: The alien instance to configure
        ai_settings: Game settings containing health configurations
    """
    if isinstance(alien, AlienL2):
        alien.health = ai_settings.alien_l2_health
    else:
        alien.health = ai_settings.alien_l1_health

def validate_alien_settings(ai_settings: AISettings) -> None:
    """
    Validate that alien settings are properly configured.
    
    Args:
        ai_settings: Game settings to validate
        
    Raises:
        ValueError: If any required settings are missing or invalid
    """
    required_attrs = [
        ('alien_l2_spawn_chance', int, lambda x: 0 <= x <= 100),
        ('alien_l2_health', int, lambda x: x > 0),
        ('alien_l1_health', int, lambda x: x > 0)
    ]
    
    for attr_name, attr_type, validator in required_attrs:
        if not hasattr(ai_settings, attr_name):
            raise ValueError(f"Missing required setting: {attr_name}")
            
        value = getattr(ai_settings, attr_name)
        if not isinstance(value, attr_type):
            raise ValueError(
                f"Invalid type for {attr_name}: expected {attr_type}, got {type(value)}"
            )
            
        if not validator(value):
            raise ValueError(f"Invalid value for {attr_name}: {value}")

def create_alien_with_settings(
    ai_settings: AISettings,
    screen: pygame.Surface
) -> AlienProtocol:
    """
    Create an alien with appropriate settings based on spawn chance.
    
    This function handles the creation of either L1 or L2 aliens based on the
    spawn chance configuration. It validates settings, creates the appropriate
    alien type, and configures its health values.
    
    Args:
        ai_settings: Game settings containing alien configuration including:
            - alien_l2_spawn_chance: Chance (1-100) to spawn L2 alien
            - alien_l2_health: Health points for L2 aliens
            - alien_l1_health: Health points for L1 aliens
        screen: PyGame surface for rendering the alien
        
    Returns:
        AlienProtocol: A fully configured alien instance (either L1 or L2)
        
    Raises:
        ValueError: If alien settings are invalid
        RuntimeError: If alien creation fails for any reason
        
    Example:
        >>> settings = AISettings()
        >>> screen = pygame.display.set_mode((800, 600))
        >>> alien = create_alien_with_settings(settings, screen)
        >>> isinstance(alien, (AlienL1, AlienL2))
        True
    """
    try:
        # Validate settings before attempting creation
        validate_alien_settings(ai_settings)
        
        # Get the appropriate alien class to instantiate
        alien_class = determine_alien_type(ai_settings)
        
        # Create and validate alien instance
        alien = alien_class(ai_settings, screen)
        if not isinstance(alien, (AlienL1, AlienL2)):
            raise RuntimeError(
                f"Created alien has invalid type: {type(alien)}"
            )
            
        # Configure alien health based on type
        set_alien_health(alien, ai_settings)
        
        # Validate the created alien has required attributes
        if not hasattr(alien, 'health') or not isinstance(alien.health, int):
            raise RuntimeError("Created alien missing valid health attribute")
            
        if not hasattr(alien, 'rect') or not isinstance(alien.rect, pygame.Rect):
            raise RuntimeError("Created alien missing valid rect attribute")
            
        return alien
        
    except Exception as e:
        logging.error(f"Failed to create alien: {e}")
        raise RuntimeError(f"Alien creation failed: {str(e)}") from e

def create_random_alien(ai_settings, screen):
    """
    Legacy function that creates a random alien. Consider using create_alien_with_settings instead.
    """
    return create_alien_with_settings(ai_settings, screen)


def load_animations(screen: pygame.Surface) -> None:
    global animations
    # animation frames
    fire_explosion_animation = Animation("explosion4", 15, screen, settings.DEFAULT_ANIMATION_LATENCY,4)

    shield_animation = Animation("shield3", 11, screen, 0, 2.6, False, 30) # type: ignore

    animations.append(fire_explosion_animation)
    animations.append(shield_animation)


def load_credits():
    global text_lines, text_rects
    credit = """
    Developers:
        MatinAfzal, BaR1BoD, Taha Moosavi, hussain, sinapila, withpouriya, onabrcom, TahaNili

    Assets:
        Ship assets used in this game were created by "Skorpio" and are licensed under CC-BY-SA 3.0.
        You can view and download them here: https://opengameart.org/content/space-ship-construction-kit.\n
        Fire sound effect by "K.L.Jonasson", Winnipeg, Canada. Triki Minut Interactive www.trikiminut.com
        You can view and download them here: https://opengameart.org/content/sci-fi-laser-fire-sfx.\n
        Explosion sound effect by by "hosch"
        You can view and download them here: https://opengameart.org/content/8-bit-sound-effects-2\n
        Explosion animation effect by "Skorpio", licensed under CC-BY 3.0.
        You can view and download them here: https://opengameart.org/content/sci-fi-effects\n
        Heart Pickup sound by "Blender Foundation", licensed under CC-BY 3.0.
        You can view and download them here: https://opengameart.org/content/life-pickup-yo-frankie\n
        Damage sound by "TeamAlpha", licensed under CC-BY 3.0.
        You can view and download them here: https://opengameart.org/content/8-bitnes-explosion-sound-effecs\n"""

    split_lines = credit.split("\n")
    font = pygame.font.Font(None, 24)
    offset = 0
    for line in split_lines:
        text = font.render(line, True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.x = 200
        text_rect.y = 100 + offset
        text_lines.append(text)
        text_rects.append(text_rect)
        offset += 20


def update_game_sprites(
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
):
    ship.update()
    update_bullets(
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
    )
    update_aliens(ai_settings, stats, ship, aliens, cargoes, health)
    update_hearts(ship, health, hearts, aliens)
    update_shields(ship, shields, health, aliens)


def check_events(ai_settings, input, screen, stats, ship, bullets, difficulty_screen=None):
    """Respond to key presses and mouse events."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    check_key_events(input, ship)
    check_mouse_events(ai_settings, input, screen, stats, ship, bullets, difficulty_screen)


def check_key_events(input, ship):
    """Handle key down/up"""

    if input.is_key_pressed(pygame.K_q):
        pygame.quit()
        sys.exit()

    ship.moving_right = True if input.is_key_down(pygame.K_RIGHT) or input.is_key_down(pygame.K_d) else False
    ship.moving_left = True if input.is_key_down(pygame.K_LEFT) or input.is_key_down(pygame.K_a) else False
    ship.moving_up = True if input.is_key_down(pygame.K_UP) or input.is_key_down(pygame.K_w) else False
    ship.moving_down = True if input.is_key_down(pygame.K_DOWN) or input.is_key_down(pygame.K_s) else False

    if input.is_key_down(pygame.K_ESCAPE):
        sys.exit()


def check_mouse_events(ai_settings, input, screen, stats, ship, bullets, difficulty_screen=None):
    """Handle mouse button press and movement."""

    if input.is_mouse_button_pressed(0):
        if stats.game_active:
            fire_bullet(ship, bullets)
        elif difficulty_screen and difficulty_screen.active:
            # Get the current mouse position
            mouse_pos = pygame.mouse.get_pos()
            # Pass the click to the difficulty screen
            difficulty_screen.handle_click(mouse_pos)


def run_play_button(ai_settings, stats, ship, aliens, cargoes, bullets, health, region_manager):
    """start a new game when the player clicks play."""
    # reset the game settings.
    ai_settings.initialize_dynamic_settings()

    # Hide the mouse cursor.
    pygame.mouse.set_visible(False)
    # Reset the game statistics.
    stats.reset()
    stats.game_active = True

    # Empty the list of aliens and bullets.
    aliens.empty()
    bullets.empty()
    cargoes.empty()

    # Center the ship.
    ship.center_ship()

    # Make health full
    health.reset()

    region_manager.reset()


def run_credit_button(stats):
    stats.credits_active = True


def run_back_button(stats):
    stats.credits_active = False


def update_screen(
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
):
    """Update image on the screen and flip to the new screen."""
    region_manager.update(screen, stats.score, ai_settings.delta_time)

    # Redraw all bullets behind ship and aliens.
    for bullet in bullets.sprites():
        # TODO: There is an interesting bug in here!
        try:
            bullet.draw()
        except:
            # print("HERE")
            pass

    for bullet in alien_bullets.sprites():
        bullet.draw()

    for heart in hearts.sprites():
        heart.draw()

    for shield in shields.sprites():
        shield.draw()

    ship.bltime()
    aliens.draw(screen)
    cargoes.draw(screen)
    health.draw()

    # Draw the score information.
    sb.show()

    # Draw the play button.
    play_button.update()
    credits_button.update()

    if stats.credits_active:
        back_button.update()
        i = 0
        for line in text_lines:
            screen.blit(line, text_rects[i])
            i += 1

    if stats.game_active:
        crosshair = TextureAtlas.get_sprite_texture("misc/crosshair.png")
        screen.blit(crosshair, pygame.mouse.get_pos())

    animations[1].set_position(ship.rect.x, ship.rect.y)
    animations[1].play()

    pygame.display.flip()


def fire_bullet(ship, bullets) -> None:
    """Fire a bullet if limit not reached yet."""
    # Create a new bullet and add it to the bullets group.
    if len(bullets) < settings.BULLETS_ALLOWED:
        new_bullet = ShipBullet(ship)
        bullets.add(new_bullet)
        sound_fire.play()


def update_bullets(
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
):
    """Update position of bullets and get rid of old bullets."""
    bullets.update()
    alien_bullets.update()

    # Get rid of bullets that have disappeared
    all_bullets = bullets.copy()
    all_bullets.add(alien_bullets.copy())

    for bullet in all_bullets:
        if (
            bullet.rect.bottom <= 0
            or bullet.rect.top >= ai_settings.screen_height
            or bullet.rect.left < 0
            or bullet.rect.right > ai_settings.screen_width
        ):
            bullets.remove(bullet)

    check_bullet_alien_collisions(
        ai_settings,
        screen,
        stats,
        sb,
        ship,
        aliens,
        bullets,
        cargoes,
        animations,
    )
    check_bullet_ship_collisions(ai_settings, screen, stats, health, ship, aliens, alien_bullets, cargoes)


def check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes, animations):
    """Respond to bullet-alien collisions."""
    # Remove any bullets and aliens that have collided.
    # Check for any bullets that have hit aliens.
    # If so, get rid of the bullet and the alien.
    collisions_1 = pygame.sprite.groupcollide(bullets, aliens, True, False)
    collisions_2 = pygame.sprite.groupcollide(bullets, cargoes, True, True)
    collisions_3 = pygame.sprite.groupcollide(aliens, cargoes, False, True)

    # if we hit alien
    if collisions_1:
        for aliens_hit in collisions_1.values():
            for alien in aliens_hit:
                alien.health -= 1
                animations[0].set_position(alien.rect.x, alien.rect.y)
                animations[0].play()
                if alien.health <= 0:
                    aliens.remove(alien)

            stats.score += ai_settings.alien_points * len(aliens)
            sb.update()
            sound_explosion.play()

    # if we hit cargo:
    if collisions_2:
        for _ in collisions_2.values():
            stats.score -= ai_settings.cargo_points
            sb.update()
            sound_explosion.play()

    # if cargo hit alien:
    if collisions_3:
        for _ in collisions_3.values():
            stats.score -= ai_settings.cargo_points
            sb.update()
            sound_explosion.play()


def check_bullet_ship_collisions(ai_settings, screen, stats, health, ship, aliens, alien_bullets, cargoes):
    """Respond to bullet-ship collisions."""
    collisions = pygame.sprite.spritecollideany(ship, alien_bullets)

    # if alien hit us
    if collisions:
        sound_damage.play()
        alien_bullets.remove(collisions)
        health.decrease(stats)


def create_alien_at_row(ai_settings, screen):
    """Create an alien and place it in the row."""
    if randint(1, 100) <= ai_settings.alien_l2_spawn_chance:
        alien = AlienL2(ai_settings, screen)
    else:
        alien = AlienL1(ai_settings, screen)

    return alien


def create_cargo(ai_settings, screen, cargoes):
    """Create a cargo and place it in the aliens."""
    cargo = CargoAlien(ai_settings, screen)
    cargoes.add(cargo)


def get_spawn_position(screen_width: int, screen_height: int) -> tuple[str, float, float]:
    """
    Determine a valid spawn position for an alien at a screen edge.
    
    Args:
        screen_width: Width of game screen in pixels
        screen_height: Height of game screen in pixels
        
    Returns:
        tuple containing:
        - direction: String indicating which edge ("top", "bottom", "left", "right")
        - x: X coordinate for spawn position
        - y: Y coordinate for spawn position
    """
    # Calculate spawn positions with proper offset to ensure aliens start off-screen
    OFFSET = 50  # pixels off screen
    
    spawn_pos = {
        "top": (
            randint(OFFSET, screen_width - OFFSET),  # Avoid corners
            -OFFSET
        ),
        "bottom": (
            randint(OFFSET, screen_width - OFFSET),
            screen_height + OFFSET
        ),
        "left": (
            -OFFSET,
            randint(OFFSET, screen_height - OFFSET)
        ),
        "right": (
            screen_width + OFFSET,
            randint(OFFSET, screen_height - OFFSET)
        )
    }
    
    direction = choice(list(spawn_pos.keys()))
    x, y = spawn_pos[direction]
    
    # Log spawn event for debugging
    logging.debug(f"Generated spawn point: direction={direction}, pos=({x}, {y})")
    
    return direction, x, y

def get_difficulty_manager():
    """
    Get or create a DifficultyManager instance with proper error handling.
    
    Returns:
        A configured difficulty manager instance
        
    Raises:
        RuntimeError: If difficulty manager creation fails
    """
    from src.difficulty_manager import DifficultyManager
    
    try:
        # Try getting existing manager from different scopes
        difficulty_manager = globals().get('difficulty_manager')
        if difficulty_manager is None:
            import __main__
            difficulty_manager = getattr(__main__, 'difficulty_manager', None)
            
        # Create new if none found
        if difficulty_manager is None:
            difficulty_manager = DifficultyManager()
            logging.info("Created new DifficultyManager instance")
            
        return difficulty_manager
        
    except Exception as e:
        logging.error(f"Failed to get/create difficulty manager: {e}")
        raise RuntimeError(f"Difficulty manager initialization failed: {e}") from e

def spawn_random_alien(ai_settings: AISettings, screen: pygame.Surface, 
                      aliens: pygame.sprite.Group) -> None:
    """
    Spawn an alien at a random edge of the screen with proper difficulty settings.
    
    This function handles:
    1. Getting/creating the difficulty manager
    2. Creating an alien with appropriate difficulty settings
    3. Positioning the alien at a valid spawn point
    4. Adding the alien to the game's alien group
    
    Args:
        ai_settings: Game settings instance
        screen: PyGame display surface
        aliens: Group to add the spawned alien to
        
    Raises:
        RuntimeError: If alien creation or spawning fails
        AttributeError: If alien lacks required position attributes
    """
    try:
        # Get difficulty manager and create alien
        difficulty_manager = get_difficulty_manager()
        from typing import cast, Any
        from pygame import Rect
        from src.alien import Alien
        
        # Create alien with difficulty settings
        alien = cast(Alien, difficulty_manager.create_alien(
            lambda: cast(Any, create_alien_with_settings(ai_settings, screen))
        ))
        
        # Get spawn position
        direction, x, y = get_spawn_position(ai_settings.screen_width, ai_settings.screen_height)
        
        # Set alien position
        if not isinstance(getattr(alien, 'rect', None), Rect):
            raise AttributeError("Alien rect attribute is not a pygame.Rect")
            
        # Update position attributes
        alien.rect.x = x  # type: ignore
        alien.rect.y = y  # type: ignore
        
        # Initialize floating point position tracking
        alien.x = float(x)  # type: ignore
        alien.y = float(y)  # type: ignore
            
        # Add alien to group
        aliens.add(alien)
        
    except Exception as e:
        logging.error(f"Failed to spawn alien: {e}")
        raise

    # Add the alien to the group
    aliens.add(alien)


def ship_hit(ai_settings, stats, screen, ship, aliens, bullets, cargoes):
    """Respond to ship being hit by alien."""
    if stats.ships_left > 0:
        # Decrement ships_left.
        stats.ships_left -= 1

        # Empty the list of aliens and bullets.
        aliens.empty()
        bullets.empty()

        # Center the ship.
        ship.center_ship()

        # Pause
        sleep(0.5)
    else:
        stats.game_active = False
        pygame.mouse.set_visible(True)


def update_aliens(ai_settings, stats, ship, aliens, cargoes, health):
    """Check if the fleet is at the edge, and then update the position of all aliens in the fleet."""
    aliens.update(ship)
    cargoes.update()

    check_collideany_ship_alien = pygame.sprite.spritecollideany(ship, aliens)
    if check_collideany_ship_alien:
        sound_explosion.play()
        aliens.remove(check_collideany_ship_alien)
        health.decrease(stats)

    check_collideany_ship_cargoes = pygame.sprite.spritecollideany(ship, aliens)
    if check_collideany_ship_cargoes:
        sound_explosion.play()
        aliens.remove(check_collideany_ship_cargoes)
        health.decrease(stats)

    remove_offscreen_aliens(aliens, ai_settings.screen_width, ai_settings.screen_height)


def alien_fire(ai_settings, stats, screen, aliens, alien_bullets, ship):
    if stats.game_active:
        for alien in aliens.sprites():
            if type(alien) is AlienL1:
                if randint(1, 1000) <= ai_settings.alien_fire_chance:
                    bullet = AlienBullet(alien, ship)
                    alien_bullets.add(bullet)
            elif type(alien) is AlienL2:
                if randint(1, 1000) <= ai_settings.alien_l2_fire_chance:
                    bullet = AlienBullet(alien, ship)
                    alien_bullets.add(bullet)


def generate_heart(
    stats: GameStats,
    screen: pygame.Surface,
    heart_group: pygame.sprite.Group,
) -> None:
    """."""
    if stats.game_active and randint(1, 1000) <= GENERATE_HEART_CHANCE:
        heart = Heart(screen)
        heart_group.add(heart)


def update_hearts(ship, health, hearts, aliens=None):
    hearts.update()

    # Ship picks up heart
    check_collideany_ship_hearts = pygame.sprite.spritecollideany(ship, hearts)
    if check_collideany_ship_hearts:
        sound_life.play()
        hearts.remove(check_collideany_ship_hearts)
        health.increase()

    # Aliens can also pick up hearts if item_agent allows
    if aliens is not None:
        collisions = pygame.sprite.groupcollide(aliens, hearts, False, False)
        for alien, hearts_hit in collisions.items():
            for heart in hearts_hit:
                try:
                    if should_pickup(alien, 'heart'):
                        on_pickup(alien, 'heart')
                        hearts.remove(heart)
                except Exception:
                    # keep game robust if item agent fails
                    pass

    for heart in hearts.copy():
        if heart.rect.bottom <= 0:
            hearts.remove(heart)


def generate_shields(screen, ai_settings, stats, shield_group):
    if stats.game_active:
        if randint(1, 1000) <= GENERATE_SHIELD_CHANCE:
            shield = Shield()
            shield_group.add(shield)


def update_shields(ship, shields, health, aliens=None):
    shields.update()

    # Ship picks up shield
    check_collideany_ship_shields = pygame.sprite.spritecollideany(ship, shields)
    if check_collideany_ship_shields:
        health.activate_shield()  # freezing health bar.
        sound_shield_fill.play()
        animations[1].set_visibility(True, True, 10, sound_shield_empty)
        shields.remove(check_collideany_ship_shields)

    # Aliens can also pick up shields if allowed by item_agent
    if aliens is not None:
        collisions = pygame.sprite.groupcollide(aliens, shields, False, False)
        for alien, shields_hit in collisions.items():
            for shield in shields_hit:
                try:
                    if should_pickup(alien, 'shield'):
                        on_pickup(alien, 'shield')
                        shields.remove(shield)
                except Exception:
                    pass

    for shield in shields.copy():
        if shield.rect.bottom <= 0:
            shield.remove(shields)


def remove_offscreen_aliens(
    aliens: pygame.sprite.Group,
    screen_width: int,
    screen_height: int,
    margin: int = 100
) -> None:
    """
    Remove aliens that have moved too far off screen.
    
    This function checks if aliens have moved beyond the screen bounds plus a margin,
    and removes them from the game if they have. The margin allows aliens to move
    slightly off screen before being removed, which looks more natural.
    
    Args:
        aliens: The sprite group containing all active aliens
        screen_width: Width of the game screen
        screen_height: Height of the game screen
        margin: Extra distance beyond screen edges before removing (default: 100px)
        
    Note:
        Uses a copy of the sprite group to safely modify while iterating
    """
    # Calculate screen bounds with margin
    min_x = -margin
    max_x = screen_width + margin
    min_y = -margin
    max_y = screen_height + margin
    
    # Check each alien's position
    for alien in aliens.copy():
        if not hasattr(alien, 'rect'):
            # Remove invalid aliens that somehow got in without a rect
            aliens.remove(alien)
            logging.warning("Removed invalid alien without rect attribute")
            continue
            
        # Remove if completely outside the screen bounds + margin
        if (alien.rect.right < min_x or
            alien.rect.left > max_x or
            alien.rect.bottom < min_y or
            alien.rect.top > max_y):
            
            aliens.remove(alien)
            logging.debug(
                f"Removed offscreen alien at ({alien.rect.x}, {alien.rect.y})"
            )
