from settings import *
from os.path import join
import pygame


def import_image(*path, format='png', alpha=True):
    """
    Function for a covinient image importing into the game
    :param path: system path for the images
    :param format: png/jpg etc.
    :param alpha: does it have transparent pixels? (default=True)
    :return: returns a loaded in picture with a conversion of the transparent pixels
    """
    full_path = join(*path) + f'.{format}'
    return pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()


class SpriteSheet:
    def __init__(self, sheet, width, height, scale=1, format='png'):
        """
        Handles proper spritesheet loading and splitting then into separate images
        :param sheet: whole spritesheet
        :param width: spritesheet width
        :param height: spritesheet height
        :param scale: spritesheet scale (scales as the settings.py atribute SCALE)
        :param format: png/jpg etc.
        """
        self.sheet = sheet
        self.width = width
        self.height = height
        self.scale = scale

    def load_all_frames(self, count):
        return [self.get_frame(i) for i in range(count)]

    def get_frame(self, index):
        frame = pygame.Surface((self.width, self.height),
                               pygame.SRCALPHA)  # creates a surface without transparent pixels
        frame.blit(self.sheet, (0, 0), (index * self.width, 0, self.width, self.height))
        size = (int(self.width * SCALE * self.scale), int(self.height * SCALE * self.scale))
        return pygame.transform.scale(frame, size)


def load_frames(sheet, count, width, height, scale=1):
    return SpriteSheet(sheet, width, height, scale).load_all_frames(count)
