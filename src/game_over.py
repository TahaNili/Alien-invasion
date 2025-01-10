import pygame

class GameOver:
    """A class to manage the game over screen."""
    
    def __init__(self, screen, stats):
        """Initialize game over screen attributes."""
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.stats = stats
        
        # Font settings for game over message
        self.text_color = (255, 0, 0)  # Red color for game over
        self.font = pygame.font.SysFont(None, 96)
        self.score_font = pygame.font.SysFont(None, 48)
        
        # Button settings
        self.button_width = 200
        self.button_height = 50
        self.button_color = (30, 30, 100)  # Dark blue
        self.button_hover_color = (50, 50, 150)  # Lighter blue for hover
        self.button_text_color = (200, 200, 255)  # Light blue text
        self.button_font = pygame.font.SysFont(None, 36)
        
        # Create button rect
        self.button_rect = pygame.Rect(0, 0, self.button_width, self.button_height)
        self.button_rect.centerx = self.screen_rect.centerx
        self.button_rect.centery = self.screen_rect.centery + 120
        
        # Button state
        self.is_button_hovered = False
        
        # Prepare the game over message and button
        self.prep_game_over()
        self.prep_final_score()
        self.prep_button("PLAY AGAIN")
        
    def prep_game_over(self):
        """Turn the game over message into a rendered image."""
        self.game_over_image = self.font.render("GAME OVER", True, self.text_color)
        self.game_over_rect = self.game_over_image.get_rect()
        self.game_over_rect.centerx = self.screen_rect.centerx
        self.game_over_rect.centery = self.screen_rect.centery - 50
        
    def prep_final_score(self):
        """Turn the final score into a rendered image."""
        final_score = f"Final Score: {self.stats.score}"
        self.final_score_image = self.score_font.render(final_score, True, self.text_color)
        self.final_score_rect = self.final_score_image.get_rect()
        self.final_score_rect.centerx = self.screen_rect.centerx
        self.final_score_rect.centery = self.screen_rect.centery + 50
        
    def prep_button(self, msg):
        """Prepare the button image."""
        self.button_text = self.button_font.render(msg, True, self.button_text_color)
        self.button_text_rect = self.button_text.get_rect()
        self.button_text_rect.center = self.button_rect.center
        
    def handle_event(self, event):
        """Handle mouse events for the button."""
        if event.type == pygame.MOUSEMOTION:
            # Check if mouse is over button
            self.is_button_hovered = self.button_rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_button_hovered:
                return True
        return False
        
    def draw(self):
        """Draw game over message, final score, and button to the screen."""
        # Draw game over text and score
        self.screen.blit(self.game_over_image, self.game_over_rect)
        self.screen.blit(self.final_score_image, self.final_score_rect)
        
        # Draw button with hover effect
        button_color = self.button_hover_color if self.is_button_hovered else self.button_color
        pygame.draw.rect(self.screen, button_color, self.button_rect)
        
        # Add a subtle border to the button
        pygame.draw.rect(self.screen, self.button_text_color, self.button_rect, 2)
        
        # Draw button text
        self.screen.blit(self.button_text, self.button_text_rect)