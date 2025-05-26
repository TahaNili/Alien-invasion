import os
import pygame
import logging

from typing import Optional
from pygame.mixer import Channel, Sound
from pathlib import Path
from ..settings import SOUNDS_DIR


SUPPORTED_FORMATS: list[str] = ["mp3", "wav", "ogg", "flac"]


class SoundManager:
    __instance = None # Singleton instance
    __logger: logging.Logger = logging.getLogger(__name__)

    @staticmethod
    def init(max_channels: int = 16) -> None:
        """
        Initializes the SoundManager singleton instance with the given number of mixer channels.
        """
        if SoundManager.__instance is None:
            SoundManager.__instance = SoundManager(max_channels)
        else:
            SoundManager.__logger.error("SoundManger is already initialized.")

    @staticmethod
    def get_instance() -> "SoundManager":
        """
        Returns the singleton instance of SoundManager. Raises an exception if not initialized.
        """
        if SoundManager.__instance is None:
            raise Exception("SoundManager not initialized. Call SoundManager.init() first.")
        return SoundManager.__instance

    @staticmethod
    def play_sound(name: str, fade_ms: int = 0) -> None:
        """
        Plays a sound by name with optional fade-in.
        """
        SoundManager.get_instance().__play_sound(name, fade_ms)

    @staticmethod
    def stop_sound(name: str, fade_ms: int = 0) -> None:
        """
        Stops a specific sound by name with optional fade-out.
        """
        SoundManager.get_instance().__stop_sound(name, fade_ms)

    @staticmethod
    def stop_all_sounds(fade_ms: int = 0) -> None:
        """
        Stops all currently playing sounds with optional fade-out.
        """
        for sound in SoundManager.get_instance().sounds.keys():
            SoundManager.stop_sound(sound, fade_ms)

    @staticmethod
    def set_volume(name: str, volume: float) -> None:
        """
        ets the volume of a specific sound. Volume must be in the range 0.0 to 1.0.
        """
        SoundManager.get_instance().__set_sound_volume(name, volume)

    @staticmethod
    def set_global_volume(volume: float) -> None:
        """
        Sets the volume for all loaded sounds.
        """
        for sound in SoundManager.get_instance().sounds.keys():
            SoundManager.set_volume(sound, volume)

    @staticmethod
    def mute_sound(name: str) -> None:
        """
         Mutes a specific sound.
        """
        SoundManager.set_volume(name, 0.0)

    @staticmethod
    def mute_all_sounds() -> None:
        """
        Mutes all sounds.
        """
        SoundManager.set_global_volume(0.0)


    # ----- INSTANCE Methods -----


    def __init__(self, max_channels: int, initial_sound_volume: float = 0.5):
        """
        Initializes the internal state, sets up mixer channels and loads available sounds.
        """
        pygame.mixer.init()

        self.sounds: dict[str, Sound] = {}
        self.channels: dict[str, Channel] = {}
        self.initial_sound_volume: float = initial_sound_volume

        pygame.mixer.set_num_channels(max_channels)
        self.available_channels: list[Channel] = [Channel(i) for i in range(max_channels)]

        self.__load_sounds()

    def __load_sound(self, path: Path) -> Optional[Sound]:
        """
        Loads a single sound file and sets its volume. Returns None if loading fails.
        """
        try:
            sound: Sound = Sound(path)
            sound.set_volume(self.initial_sound_volume)
            return sound
        except Exception as e:
            SoundManager.__logger.error(f"Failed to load sound {path}: {e}")
            return None

    def __load_sounds(self) -> None:
        """
        Walks through the settings.SOUNDS_DIR and loads all supported audio files.
        """
        for root, _, files in os.walk(SOUNDS_DIR):
            for file in files:
                if file.split(".")[-1] in SUPPORTED_FORMATS:
                    path: Path = Path(root) / Path(file)
                    name: str = str(path.relative_to(SOUNDS_DIR))
                    sound: Sound = self.__load_sound(path)
                    if sound:
                        self.sounds[name] = sound

    def __get_free_channel(self) -> Optional[Channel]:
        """
        Returns a free mixer channel, or None if all channels are busy.
        """
        for channel in self.available_channels:
            if not channel.get_busy():
                return channel
        return None

    def __play_sound(self, name: str, fade_ms: int) -> None:
        if name in self.sounds.keys():
            channel: Channel = self.__get_free_channel()
            if channel:
                channel.play(self.sounds[name], fade_ms=fade_ms)
                self.channels[name] = channel
            else:
                SoundManager.__logger.warning("No free channel to play sound: ", name)
        else:
            SoundManager.__logger.error(f"Sound '{name}' not found.")

    def __stop_sound(self, name: str, fade_ms: int) -> None:
        channel: Channel = self.channels.get(name)
        if channel:
            if fade_ms > 0:
                channel.fadeout(fade_ms)
            else:
                channel.stop()

    def __set_sound_volume(self, sound_name: str, volume: float) -> None:
        volume = max(0.0, min(1.0, volume)) # Clamps the value to the 0.0 - 1.0 range.
        sound: Sound = self.sounds.get(sound_name)
        if sound:
            sound.set_volume(volume)
