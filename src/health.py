import pygame


class Health:
    """A class for managing and show ship lives."""

    def __init__(self, ai_settings, screen):
        """Initialize class properties."""
        self.screen = screen
        self.max_hearts = ai_settings.max_hearts
        self.init_hearts = ai_settings.init_hearts
        self.current_hearts = 0

    def init_health(self):
        """Reset health."""
        self.current_hearts = self.init_hearts

    def full_health(self):
        self.current_hearts = self.max_hearts

    def increase_health(self):
        """Increase health by one if it is less than maximum hearts."""

        if self.current_hearts + 1 <= self.max_hearts:
            self.current_hearts += 1

    def decrease_health(self, stats):
        """Decrease health by one."""

        self.current_hearts -= 1
        if self.current_hearts == 0:
            stats.game_active = False
            pygame.mouse.set_visible(True)

    def show_health(self):
        """Display health bar on top left corner of the screen."""

        heart_size = 20
        heart_full = pygame.image.load('data/assets/hearts/full_heart.png')
        heart_empty = pygame.image.load('data/assets/hearts/empty_heart.png')
        
        heart_full = pygame.transform.scale(heart_full, (heart_size, heart_size))
        heart_empty = pygame.transform.scale(heart_empty, (heart_size, heart_size))
        health_rect = self.screen.get_rect()
        health_rect.top = 20
        health_rect.left = 20
        for i in range(1, self.max_hearts + 1):
            if i <= self.current_hearts:
                self.screen.blit(heart_full, health_rect)
            else:
                self.screen.blit(heart_empty, health_rect)
            health_rect.left = health_rect.left + 25
