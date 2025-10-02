"""
DifficultyScreen module for handling difficulty selection UI
"""
from dataclasses import dataclass
from typing import Callable, Dict

import pygame

from src.settings import FONT, SCREEN_HEIGHT, SCREEN_WIDTH
from src.entities.ui.elements.button import Button, BtnColors

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
        
        # Calculate button positions
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - 200
        button_spacing = 80
        button_size = (240, 64)
        
        # Create difficulty buttons
        difficulties = ["Easy", "Normal", "Hard", "VeryHard", "Unbeatable"]
        self.buttons = {}
        
        for i, diff in enumerate(difficulties):
            button_y = start_y + (i * button_spacing)
            self.buttons[diff] = Button(
                text=diff,
                size=button_size,
                pos=(center_x - button_size[0]//2, button_y),
                on_click=lambda d=diff: self._on_difficulty_selected(d),
                show_fn=lambda: self.active
            )
    
    def show(self):
        """Display the difficulty selection screen"""
        self.active = True
    
    def hide(self):
        """Hide the difficulty selection screen"""
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
            
        # Draw semi-transparent background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw title
        title = FONT.render("Select Difficulty", True, BtnColors.TEXT_COLOR)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Update all buttons
        for button in self.buttons.values():
            button.update()