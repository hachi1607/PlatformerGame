from settings import *
from sprites import *

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Platformer')
        self.clock = pygame.time.Clock()
        self.running = True

        # groups
        self.all_sprites = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group()

        #load_game
        self.setup()

    def setup(self):
        tmx_map = load_pygame(join('Assety do gry', 'maps', 'world.tmx'))

        # In your Game.setup() method:
        for x, y, image in tmx_map.get_layer_by_name('Main').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, (self.all_sprites, self.collision_sprites))

        decor_layer = tmx_map.get_layer_by_name('Decorations')
        for x, y, image in decor_layer.tiles():

            pixel_x = x * TILE_SIZE
            pixel_y = (y * TILE_SIZE) - image.get_height() + TILE_SIZE
            Sprite((pixel_x, pixel_y), image, (self.all_sprites, self.collision_sprites))

    def run(self):
        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # updating
            self.all_sprites.update(dt)

            self.display_surface.fill(BG_COLOR)

            self.all_sprites.draw(self.display_surface)
            sprite = pygame.image.load("Tile_02.png").convert_alpha()
            sprite_rect = sprite.get_frect(topleft=(5, 5))

            self.display_surface.blit(sprite, sprite_rect)
            pygame.display.update()

        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
