"""Define a customizable button class for Pygame with hover and click effects."""

import pygame
from pygame.locals import MOUSEBUTTONDOWN


class Button:
    """Represents a clickable button with hover effects."""

    def __init__(
        self,
        screen: pygame.Surface,
        position: tuple[int, int],
        size: tuple[int, int],
        text: str,
        font: pygame.font.Font = None,
        fg_color: tuple[int, int, int] = (255, 255, 255),
        bg_color: tuple[int, int, int] = (0, 0, 0),
        border_width: int = 1,
        border_color: tuple[int, int, int] = (255, 255, 255),
        action: callable[[], None] | None = None,
        hover_color_factor: float = 1.2,
    ) -> None:
        """Initialize the button.

        :param screen: The Pygame screen where the button will be drawn.
        :param position: A tuple (x, y) for the button's position.
        :param size: A tuple (width, height) for the button's size.
        :param text: The text displayed on the button.
        :param font: Font for the text (optional).
        :param fg_color: Foreground (text) color.
        :param bg_color: Background color of the button.
        :param border_width: Width of the button's border.
        :param border_color: Color of the button's border.
        :param action: Function to be called when the button is clicked.
        :param hover_color_factor: Factor to change the background color on hover.
        """
        self.screen = screen
        self.position = pygame.Rect(position, size)
        self.text = text
        self.font = font or pygame.font.Font(None, 36)
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.border_width = border_width
        self.border_color = border_color
        self.action = action
        self.hover_color_factor = hover_color_factor
        self.original_bg_color = pygame.Color(*bg_color)
        self.hover_bg_color = self.original_bg_color.copy()
        self.hover_bg_color.hsva = (
            self.original_bg_color.hsva[0],
            min(100, self.original_bg_color.hsva[1] * hover_color_factor),
            self.original_bg_color.hsva[2],
        )

    def update(self, event: pygame.event.Event) -> None:
        """Update button state (check hover and click)."""
        self.check_hover()
        self.handle_click(event)
        self.draw()

    def check_hover(self) -> None:
        """Check if the mouse is hovering over the button."""
        if self.position.collidepoint(pygame.mouse.get_pos()):
            self.bg_color = self.hover_bg_color
        else:
            self.bg_color = self.original_bg_color

    def handle_click(self, event: pygame.event.Event) -> None:
        """Handle mouse click event."""
        if (
            event.type == MOUSEBUTTONDOWN
            and event.button == 1
            and self.position.collidepoint(event.pos)
            and self.action
        ):
            self.action()

    def draw(self) -> None:
        """Draw the button on the screen."""
        pygame.draw.rect(self.screen, self.bg_color, self.position)
        if self.border_width > 0:
            pygame.draw.rect(self.screen, self.border_color, self.position, self.border_width)
        self.draw_text()

    def draw_text(self) -> None:
        """Draw the button's text centered on the button."""
        text_surface = self.font.render(self.text, True, self.fg_color)
        text_rect = text_surface.get_rect(center=self.position.center)
        self.screen.blit(text_surface, text_rect)
