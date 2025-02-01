import time
import pygame


class Animation:
    def __init__(self, frame_path, frame_count, screen):
        self.animation_frames = []
        self.animation_rects = []
        self.screen = screen

        self.animation_position_x = 0
        self.animation_position_y = 0

        self.animation_latency = 0.0001

        temp_path = frame_path
        for i in range(1, frame_count + 1):
            temp_path = temp_path + f"/f{i}.png"
            loaded_frame = pygame.image.load(temp_path)
            loaded_frame = pygame.transform.scale(loaded_frame, (loaded_frame.get_width() / 4,
                                                                 loaded_frame.get_height() / 4))
            self.animation_frames.append(loaded_frame)
            self.animation_rects.append((loaded_frame.get_rect()))
            temp_path = frame_path  # reset to actual path.

    def set_position(self, x, y):
        self.animation_position_x = x
        self.animation_position_y = y

    def play(self):
        i = 0
        for frame in self.animation_frames:
            current_rect = self.animation_rects[i]
            current_rect.x = self.animation_position_x
            current_rect.y = self.animation_position_y
            self.screen.blit(frame, current_rect)
            i += 1
            pygame.display.update(self.animation_rects)
            time.sleep(self.animation_latency)  # TODO: Find a better solution.
