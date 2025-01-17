import sys
import pygame
from time import sleep
from random import randint,choice
from src.bullet import ShipBullet, AlienBullet
from src.alien import CargoAlien, AlienL1, AlienL2
from src.heart import Heart

pygame.mixer.init()

sound_fire = pygame.mixer.Sound('data/assets/sounds/fire.ogg')
sound_explosion = pygame.mixer.Sound('data/assets/sounds/explosion.ogg')
one_time_do_bullet_hit_flag = False

def load_sounds():
    global sound_fire, sound_explosion
    sound_fire = pygame.mixer.Sound('data/assets/sounds/fire.ogg')
    sound_explosion = pygame.mixer.Sound('data/assets/sounds/explosion.ogg')


def update_game_sprites(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes, alien_bullets, health, hearts):
    ship.update()
    update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes, alien_bullets, health)
    update_aliens(ai_settings, stats, ship, aliens, cargoes, health)
    update_hearts(ship, health, hearts)


def check_keydown_events(event, ship):
    if event.key == pygame.K_q:
        sys.exit()

    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
        ship.moving_right = True

    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
        ship.moving_left = True

    if event.key == pygame.K_UP or event.key == pygame.K_w:
        ship.moving_up = True

    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
        ship.moving_down = True


def fire_bullet(ai_settings, screen, ship, bullets):
    """Fire a bullet if limit not reached yet."""
    # Create a new bullet and add it to the bullets group.
    if len(bullets) < ai_settings.bullets_allowed:
        new_bullet = ShipBullet(ai_settings, screen, ship)
        bullets.add(new_bullet)
        sound_fire.play()


def check_keyup_events(event, ship):
    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
        ship.moving_right = False

    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
        ship.moving_left = False

    if event.key == pygame.K_UP or event.key == pygame.K_w:
        ship.moving_up = False

    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
        ship.moving_down = False

    
def check_events(ai_settings, screen, stats, play_button, ship, aliens, bullets, cargoes, health):
    """Respond to key presses and mouse events."""
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            sys.exit()

        elif event.type == pygame.KEYDOWN:
            check_keydown_events(event, ship)

        elif event.type == pygame.KEYUP:
            check_keyup_events(event, ship)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if stats.game_active:
                fire_bullet(ai_settings, screen, ship, bullets)
            else:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                check_play_button(ai_settings, stats, play_button, ship, aliens, bullets, cargoes, health, mouse_x, mouse_y)


def check_play_button(ai_settings, stats, play_button, ship, aliens, cargoes, bullets, health, mouse_x, mouse_y):
    """start a new game when the player clicks play."""
    button_clicked = play_button.rect.collidepoint(mouse_x, mouse_y)
    if button_clicked and not stats.game_active:
        # reset the game settings.
        ai_settings.initialize_dynamic_settings()

        # Hide the mouse cursor.
        pygame.mouse.set_visible(False)
        # Reset the game statistics.
        stats.reset_stats()
        stats.game_active = True          

        # Empty the list of aliens and bullets.
        aliens.empty()
        bullets.empty()
        cargoes.empty()

        # Center the ship.
        ship.center_ship()

        # Make health full
        health.init_health()


def update_screen(ai_settings, screen, stats, sb, ship, aliens, bullets, play_button, screen_bg, screen_bg_2, cargoes,alien_bullets, health, hearts):
    """Update image on the screen and flip to the new screen."""
    # Redraw the screen during each pass through the loop
    screen.fill(ai_settings.bg_color)
    screen.blit(screen_bg, (ai_settings.bg_screen_x, ai_settings.bg_screen_y))
    screen.blit(screen_bg_2, (ai_settings.bg_screen_2_x, ai_settings.bg_screen_2_y))

    # Redraw all bullets behind ship and aliens.
    for bullet in bullets.sprites():
        # TODO: There is an interesting bug in here!
        try:
            bullet.draw_bullet()
        except:
            pass
    
    for bullet in alien_bullets.sprites():
        bullet.draw_bullet()

    for heart in hearts.sprites():
        heart.draw_heart()

    ship.bltime()
    aliens.draw(screen)
    cargoes.draw(screen)
    health.show_health()

    # Draw the score information.
    sb.show_score()

    # Draw the play button if the game is inactive
    if not stats.game_active:
        play_button.draw_button()
    else:
        # Resetting the background when it leaves screen
        if ai_settings.bg_screen_y >= ai_settings.screen_height:
            ai_settings.bg_screen_y = -ai_settings.screen_height * 2

        if ai_settings.bg_screen_2_y >= ai_settings.screen_height:
            ai_settings.bg_screen_2_y = -ai_settings.screen_height * 2

        # Updating the background when it leaves screen
        ai_settings.bg_screen_y += ai_settings.bg_screen_scroll_speed
        ai_settings.bg_screen_2_y += ai_settings.bg_screen_scroll_speed

    pygame.display.flip()


def update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes,alien_bullets, health):
    """Update position of bullets and get rid of old bullets."""
    bullets.update()
    alien_bullets.update()

    # Get rid of bullets that have disappeared
    all_bullets = bullets.copy()
    all_bullets.add(alien_bullets.copy())

    for bullet in all_bullets:
        if (bullet.rect.bottom <= 0 or bullet.rect.top >= ai_settings.screen_height or bullet.rect.left < 0
                or bullet.rect.right > ai_settings.screen_width):
            bullets.remove(bullet)

    check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes)
    check_bullet_ship_collisions(ai_settings, screen, stats, health, ship, aliens, alien_bullets, cargoes)


def check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes):
    """Respond to bullet-alien collisions."""
    # Remove any bullets and aliens that have collided.
    # Check for any bullets that have hit aliens.
    # If so, get rid of the bullet and the alien.
    collisions_1 = pygame.sprite.groupcollide(bullets, aliens, True,False)
    collisions_2 = pygame.sprite.groupcollide(bullets, cargoes, True, True)
    collisions_3 = pygame.sprite.groupcollide(aliens, cargoes, False, True)

    # if we hit alien
    if collisions_1:
        for aliens_hit in collisions_1.values():
            for alien in aliens_hit:
                alien.health -= 1
                if alien.health <= 0 :
                    aliens.remove(alien)

            stats.score += ai_settings.alien_points * len(aliens)
            sb.prep_score()
            sound_explosion.play()

    # if we hit cargo:
    if collisions_2:
        for _ in collisions_2.values():
            stats.score -= ai_settings.cargo_points
            sb.prep_score()
            sound_explosion.play()

    # if cargo hit alien:
    if collisions_3:
        for _ in collisions_3.values():
            stats.score -= ai_settings.cargo_points
            sb.prep_score()
            sound_explosion.play()


def check_bullet_ship_collisions(ai_settings, screen, stats, health, ship, aliens, alien_bullets, cargoes):
    """Respond to bullet-ship collisions."""
    collisions = pygame.sprite.spritecollideany(ship, alien_bullets)

    # if alien hit us
    if collisions:
        sound_explosion.play()
        alien_bullets.remove(collisions)
        health.decrease_health(stats)


def create_alien(ai_settings, screen):
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


def spawn_random_alien(ai_settings, screen, aliens):
    """Spawn an alien at a random edge of the screen."""
    screen_width = ai_settings.screen_width
    screen_height = ai_settings.screen_height

    # Select a random direction from which the alien will spawn
    direction = choice(['top', 'bottom', 'left', 'right'])

    if direction == 'top':  # From the top edge
        x = randint(0, screen_width)  # Random x-coordinate along the top edge
        y = -50  # Just above the screen
    elif direction == 'bottom':  
        x = randint(0, screen_width)  
        y = screen_height + 50  
    elif direction == 'left':  
        x = -50 
        y = randint(0, screen_height)  
    elif direction == 'right':  
        x = screen_width + 50 
        y = randint(0, screen_height)  

    # Create the alien and set its initial position
    alien = create_alien(ai_settings, screen)
    alien.rect.x = x
    alien.rect.y = y
    alien.x = float(alien.rect.x)
    alien.y = float(alien.rect.y)

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
        health.decrease_health(stats)

    check_collideany_ship_cargoes = pygame.sprite.spritecollideany(ship, aliens)
    if check_collideany_ship_cargoes:
        sound_explosion.play()
        aliens.remove(check_collideany_ship_cargoes)
        health.decrease_health(stats)

    remove_offscreen_aliens(aliens, ai_settings.screen_width, ai_settings.screen_height)


def update_hearts(ship, health, hearts):
    hearts.update()

    check_collideany_ship_hearts = pygame.sprite.spritecollideany(ship, hearts)
    if check_collideany_ship_hearts:
        hearts.remove(check_collideany_ship_hearts)
        health.increase_health()

    for heart in hearts.copy():
        if heart.rect.bottom <= 0:
            hearts.remove(heart)


def alien_fire(ai_settings,stats, screen, aliens, alien_bullets):
    if stats.game_active : 
        for alien in aliens.sprites():
            if type(alien) is AlienL1:
                if randint(1, 1000) <= ai_settings.alien_fire_chance:
                    bullet = AlienBullet(ai_settings, screen, alien)
                    alien_bullets.add(bullet)
            elif type(alien) is AlienL2:
                if randint(1, 1000) <= ai_settings.alien_l2_fire_chance:  
                    bullet = AlienBullet(ai_settings, screen, alien,ship)
                    alien_bullets.add(bullet)


def generate_heart(ai_settings,stats, screen, heart_group):
    if stats.game_active : 
        if randint(1, 1000) <= ai_settings.generate_heart_chance:  
            heart = Heart(ai_settings, screen)
            heart_group.add(heart)


def remove_offscreen_aliens(aliens, screen_width, screen_height):
    """"""
    for alien in aliens.copy():
        if (alien.rect.right < 0 or alien.rect.left > screen_width or
            alien.rect.bottom < 0 or alien.rect.top > screen_height):
            aliens.remove(alien)
