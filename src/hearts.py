class Hearts:
    """A class for manging and show user lives."""
    def __init__(self, ai_settings, screen):
        """Initialize class properties."""
        self.ai_settings = ai_settings
        self.screen = screen
        self.current_hearts = 0


    def initHearts(self):
        #todo: method description
        if self.ai_settings.init_hearts > self.ai_settings.max_hearts:
            return 
        self.current_hearts = self.ai_settings.init_hearts

    def fullHearts(self):
        #todo: method description
        self.current_hearts = self.ai_settings.max_hearts

    def addHeart(self):
        #todo: method description
        if self.current_hearts + 1 > self.ai_settings.max_hearts:
            return
        self.current_hearts += 1

    def minHeart(self):
        #todo: method description        
        if self.current_hearts == 1 : 
            #todo: user loss
            return 
        self.current_hearts -= 1

    def printHeartsOnScreen(self):
        pass

