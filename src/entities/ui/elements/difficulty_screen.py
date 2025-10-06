"""
DifficultyScreen module for handling difficulty selection UI
"""
from dataclasses import dataclass
from typing import Callable, Dict

import pygame

from src.settings import FONT, SCREEN_HEIGHT, SCREEN_WIDTH
from src.entities.ui.elements.button import Button as btn, BtnColors

@dataclass
class DifficultyScreen:
    """Manages the difficulty selection screen UI"""
    
    def __init__(self, on_select: Callable[[str], None], on_train: Callable[[], None] | None = None):
        """Initialize the difficulty selection screen
        
        Args:
            on_select: Callback function when difficulty is selected
        """
        self.screen = pygame.display.get_surface()
        self.on_select = on_select
        self.active = False
        
        # Standard button size like other game buttons
        button_size = (240, 64)
        
        # Button vertical spacing
        start_y = SCREEN_HEIGHT // 2 - 150
        spacing_y = 80
        
        # Create difficulty buttons centered horizontally
        center_x = SCREEN_WIDTH // 2 - 120  # Same x-position calculation as main menu buttons
        
        self.buttons = {
            "Easy": btn(
                "Easy",
                button_size,
                (center_x, start_y),
                lambda: self._on_difficulty_selected("Easy"),
                lambda: self.active
            ),
            "Normal": btn(
                "Normal", 
                button_size,
                (center_x, start_y + spacing_y),
                lambda: self._on_difficulty_selected("Normal"),
                lambda: self.active
            ),
            "Hard": btn(
                "Hard",
                button_size,
                (center_x, start_y + spacing_y * 2),
                lambda: self._on_difficulty_selected("Hard"),
                lambda: self.active
            ),
            "VeryHard": btn(
                "VeryHard",
                button_size,
                (center_x, start_y + spacing_y * 3),
                lambda: self._on_difficulty_selected("VeryHard"),
                lambda: self.active
            ),
            "Unbeatable": btn(
                "Unbeatable",
                button_size,
                (center_x, start_y + spacing_y * 4),
                lambda: self._on_difficulty_selected("Unbeatable"),
                lambda: self.active
            )
        }
        # Optional Train AI button (placed below difficulties)
        self._on_train = on_train
        self.train_button = btn(
            "Train AI",
            button_size,
            (center_x, start_y + spacing_y * 5),
            self._on_train_clicked,
            lambda: self.active,
        )
        # Temporary animated message state
        self._msg_red = None
        self._msg_green = None
        self._msg_alpha = 255
        self._msg_timer = 0
        self._msg_duration_ms = 2000
        # Training state - when True, Train button is disabled
        self._training_active = False
    
    def show(self):
        """Display the difficulty selection screen"""
        print("DEBUG: DifficultyScreen.show() called")  # Debug log
        self.active = True
        print(f"DEBUG: DifficultyScreen.active = {self.active}")  # Debug log
    
    def hide(self):
        """Hide the difficulty selection screen"""
        print("DEBUG: DifficultyScreen.hide() called")  # Debug log
        self.active = False
    
    def _on_difficulty_selected(self, difficulty: str):
        """Handle difficulty button click
        
        Args:
            difficulty: The selected difficulty level
        """
        self.hide()
        self.on_select(difficulty)
    
    def handle_click(self, pos):
        """Handle mouse click at the given position"""
        if not self.active:
            return False
            
        # Check if any button was clicked
        for button in self.buttons.values():
            if button.show_fn():  # Only check visible buttons
                button.update()  # Make sure button state is up to date
        # check train button
        if self.train_button.show_fn():
            self.train_button.update()
                
        return False  # No button was clicked

    def update(self):
        """Update and draw the difficulty screen"""
        if not self.active:
            return

        # Update button states
        for button in self.buttons.values():
            button.update()
        
        # Draw the screen (includes buttons and messages)
        self.draw(self.screen)

        # Draw temporary messages if present
        if self._msg_red or self._msg_green:
            # compute alpha fade based on timer
            self._msg_timer += int(pygame.time.get_ticks() % 1000)
            # simple fade: reduce alpha over duration
            # Note: use pygame.time.get_ticks() delta would be better, keep simple
            a = max(0, self._msg_alpha - (int(self._msg_timer / self._msg_duration_ms * 255)))
            if self._msg_red:
                surf_r = FONT.render(self._msg_red, True, (255, 50, 50))
                surf_r.set_alpha(a)
                rect_r = surf_r.get_rect(center=(SCREEN_WIDTH//2, 60))
                self.screen.blit(surf_r, rect_r)
            if self._msg_green:
                surf_g = FONT.render(self._msg_green, True, (50, 200, 50))
                surf_g.set_alpha(a)
                rect_g = surf_g.get_rect(center=(SCREEN_WIDTH//2, 100))
                self.screen.blit(surf_g, rect_g)
            if a <= 0:
                # clear messages
                self._msg_red = None
                self._msg_green = None
                self._msg_alpha = 255
                self._msg_timer = 0

    def show_temporary_message(self, red_text: str | None, green_text: str | None, duration_ms: int = 2000):
        """Show a transient red/green message on the difficulty screen."""
        self._msg_red = red_text
        self._msg_green = green_text
        self._msg_timer = pygame.time.get_ticks()  # Store current time instead of 0
        self._msg_duration_ms = duration_ms
        
    def draw(self, screen):
        """Draw the difficulty screen"""
        if not self.active:
            return

        # Draw semi-transparent background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Draw title
        title = FONT.render("Choose Difficulty Level", True, BtnColors.TEXT_COLOR)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200))
        screen.blit(title, title_rect)
        
        # Draw buttons
        for button in self.buttons.values():
            if button.show_fn():  # Only draw if button should be visible
                button.update()  # Update button state
        # draw train button
        if self.train_button.show_fn():
            self.train_button.update()
                
        # Draw messages if present
        current_time = pygame.time.get_ticks()
        if self._msg_red or self._msg_green:
            elapsed = current_time - self._msg_timer
            if elapsed < self._msg_duration_ms:
                alpha = 255 * (1 - (elapsed / self._msg_duration_ms))
                if self._msg_red:
                    surf_r = FONT.render(self._msg_red, True, (255, 50, 50))
                    surf_r.set_alpha(int(alpha))
                    rect_r = surf_r.get_rect(center=(SCREEN_WIDTH//2, 60))
                    screen.blit(surf_r, rect_r)
                if self._msg_green:
                    surf_g = FONT.render(self._msg_green, True, (50, 200, 50))
                    surf_g.set_alpha(int(alpha))
                    rect_g = surf_g.get_rect(center=(SCREEN_WIDTH//2, 100))
                    screen.blit(surf_g, rect_g)
            else:
                self._msg_red = None
                self._msg_green = None

    def _on_train_clicked(self):
        """Internal handler for Train AI button click - invokes optional on_train callback."""
        if self._on_train is None:
            # No handler provided
            self.show_temporary_message("No training handler available", None)
            return
        try:
            # Call the provided training callback (expected to be non-blocking)
            self._on_train()
            self.show_temporary_message(None, "Training started")
            self._training_active = True  # Set training active
        except Exception as e:
            self.show_temporary_message("Failed to start training", None)
        # NOTE: Do NOT clear _training_active here — background trainer should clear it

    def set_training_active(self, active: bool):
        """Set or clear the training active flag (used by external background trainer)."""
        self._training_active = bool(active)

    def clear_training_active(self):
        """Convenience to clear the training flag."""
        self._training_active = False