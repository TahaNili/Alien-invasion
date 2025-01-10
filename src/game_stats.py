class GameStats:
    """Track statistics for Alien Invasion."""

    def __init__(self, ai_settings):
        """Initialize statistics."""
        self.ai_settings = ai_settings
        self.reset_stats()

        # Start game in an inactive state.
        self.game_active = False

        # High score should never be reset
        self.high_score = self.ai_settings.high_score if hasattr(self.ai_settings, 'high_score') else 0

    def reset_stats(self):
        """Initialize statistics that can change during the game."""
        self.ships_left = self.ai_settings.ship_limit
        self.score = 0
        self.level = 1

    # def reset_stats(self):
    #     """Initialize statistics that can change during the game."""
    #     self.ships_left = self.ai_settings.ship_limit
    #     self.score = 0
