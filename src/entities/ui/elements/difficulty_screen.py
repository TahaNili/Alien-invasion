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
    
    def __init__(self, on_select: Callable[[str], None]):
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
        # Temporary animated message state
        self._msg_red = None
        self._msg_green = None
        self._msg_alpha = 255
        self._msg_timer = 0
        self._msg_duration_ms = 2000
    
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
    
    def update(self):
        """Update and draw the difficulty screen"""
        if not self.active:
            return
            
        print("DEBUG: DifficultyScreen.update() drawing...")  # Debug log
        
        # Draw semi-transparent background that blocks clicks
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Handle mouse events to prevent click-through
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        # If clicked outside any difficulty button, ignore the click
        if mouse_clicked:
            clicked_any_button = False
            for button in self.buttons.values():
                if button.top_rect.collidepoint(mouse_pos):
                    clicked_any_button = True
                    break
            if not clicked_any_button:
                # Block the click by consuming it
                pygame.event.clear(pygame.MOUSEBUTTONDOWN)
                pygame.event.clear(pygame.MOUSEBUTTONUP)
        
        # Draw title
        title = FONT.render("Choose Difficulty Level", True, BtnColors.TEXT_COLOR)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150))
        self.screen.blit(title, title_rect)
        
        # Update all buttons
        print("DEBUG: Updating difficulty buttons...")  # Debug log
        for button in self.buttons.values():
            if not button.show_fn():
                print(f"DEBUG: Button {button.text} hidden by show_fn")  # Debug log
            button.update()

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
        self._msg_alpha = 255
        self._msg_timer = 0
        self._msg_duration_ms = duration_ms