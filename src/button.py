import pygame.font


pygame.mixer.init()

class Button:
    """A class to create button.

    Args:
        screen (pygame.Surface): Game screen
        input (src.input.Input): Game input handler
        position (tuple[int, int]): Button position on screen
        size (tuple[int, int]): Button height and width
        text (str): Button text
        font (pygame.font.Font): Button text font
        foreground_color (tuple[int, int, int]): Button text color
        background_color (tuple[int, int, int]): Button background color
        border_width (int): Button border width. Set to zero for no border
        border_color (tuple[int, int, int]): Button border color
        display_condition (() -> bool): Button display condition. Leave empty to be always displayed
        on_clicked (() -> Any): A function to run when button is clicked
    """

    def __init__(self, screen, input, position=(0, 0), size=(200, 50), text="", font=None,
                 foreground_color=(255, 255, 255), background_color=(0, 0, 0), border_width=1, border_color=(255, 255, 255),
                 display_condition=None, on_clicked=None):

        self.screen = screen

        self.input = input
        self.position = position
        self.size = size
        self.text = text
        if font is None:
            self.font = pygame.font.SysFont(None, 48)
        else:
            self.font = font

        self.foreground_color = foreground_color
        self.background_color = background_color
        self.border_width = border_width
        self.border_color = border_color

        self.display_condition = display_condition
        self.on_clicked = on_clicked

        self.__sound = pygame.mixer.Sound("data/assets/sounds/button_clicked.mp3")
        self.__sound.set_volume(0.35)
        self.__original_bg_color = self.background_color
        self.__hovered_bg_color = pygame.color.Color(self.background_color[0], self.background_color[1], self.background_color[2])
        self.__hovered_bg_color = self.__hovered_bg_color.correct_gamma(2.5)

    def update(self):
        """Must be called every frame."""

        if self.input is None:
            return

        if self.__should_display():
            self.__set_hovered()
            self.__set_clicked()
            self.__draw()

    #
    #  Update helper methods
    #

    def __set_hovered(self):
        curser = self.input.get_mouse_cursor_position()

        if self.__is_with_in_bounds(curser, (self.position[0], self.position[1], self.size[0], self.size[1])):
            self.background_color = (self.__hovered_bg_color.r, self.__hovered_bg_color.g, self.__hovered_bg_color.b)
        else:
            self.background_color = self.__original_bg_color

    def __set_clicked(self):
        curser = self.input.get_mouse_cursor_position()

        if self.__is_with_in_bounds(curser, (self.position[0], self.position[1], self.size[0], self.size[1])) \
                and self.input.is_mouse_button_pressed(0):
            self.__sound.play()
            if self.on_clicked is not None:
                self.on_clicked()

    def __is_with_in_bounds(self, position, rect):
        return ((position[0] >= rect[0]) and (position[0] <= rect[0] + rect[2]) and (position[1] >= rect[1])
                and (position[1] <= rect[1] + rect[3]))

    def __draw(self):
        self.__draw_background()
        self.__draw_text()
        self.__draw_border()

    #
    #  draw helper methods
    #

    def __draw_background(self):
        """Draws the button background."""
        pygame.draw.rect(self.screen, self.background_color, (self.position[0], self.position[1], self.size[0], self.size[1]))

    def __draw_text(self):
        """Draws the button text."""
        text_image = self.font.render(self.text, True, self.foreground_color, None)
        pos = ((self.position[0] + self.size[0] / 2) - text_image.get_rect().width // 2,
               (self.position[1] + self.size[1] / 2) - text_image.get_rect().height // 2)

        self.screen.blit(text_image, pos)

    def __draw_border(self):
        """Draws the button border."""
        if self.border_width > 0:
            pygame.draw.rect(self.screen, self.border_color, (self.position[0], self.position[1], self.size[0], self.size[1]), width=self.border_width)

    def __should_display(self):
        if self.display_condition is not None:
            if type(self.display_condition) is bool:
                return self.display_condition
            else:
                return self.display_condition()
        return True