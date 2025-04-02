import pygame
from os import walk
from os.path import join
from pytmx.util_pygame import load_pygame

SCALE = 3
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
TILE_SIZE = 32
FRAMERATE = 60
BG_COLOR = '#b59588'

JUMP_HEIGHT = 11*SCALE
SPEED = 200*SCALE
GRAVITY = 25*SCALE