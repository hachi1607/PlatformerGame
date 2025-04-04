import pygame
import pytmx
from settings import *
from sprites import *
from groups import AllSprites
from support import *
from gameover import GameOver


class Game:
    def __init__(self):
        pygame.init()
        self.game_over_screen = None
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Platformer')
        self.font = pygame.font.Font('dogicapixel.ttf', 24)
        self.clock = pygame.time.Clock()

        self.running = True
        self.player_dead = False

        self.scroll = 0
        self.bg_images = []
        for i in range(1, 6):
            bg_image = import_image('Assety do gry', 'Tiles', '2 Background', 'Day', f'{i}')
            scale_factor = WINDOW_HEIGHT / bg_image.get_height()
            scaled_width = int(bg_image.get_width() * scale_factor)
            scaled_image = pygame.transform.scale(bg_image, (scaled_width, WINDOW_HEIGHT))
            self.bg_images.append(scaled_image)
        self.bg_width = self.bg_images[0].get_width()
        self.player_pos = 0

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.entities = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.health_pickups = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()

        self.score = 0

        self.enemy_spawn_points = []
        self.heart_spawn_points = []
        self.collectibles_spawn_points = []

        # countdown timer
        self.countdown_time = 15
        self.countdown_timer = None
        self.start_countdown()

        # load_game
        self.load_assets()
        self.setup()

        self.scroll -= self.player_pos

    def load_assets(self):
        """
        Groups all needed function for loading player/enemy spritesheets and other images.
        The function for importing images and splitting spritesheets into frames is in support.py
        """
        # player assets
        self.p_walk_img = import_image('Assety do gry', 'Player', 'Walk-sheet')
        self.p_idle_img = import_image('Assety do gry', 'Player', 'Idle-sheet')
        self.p_jump_img = import_image('Assety do gry', 'Player', 'Jump-sheet')
        self.p_attack_img = import_image('Assety do gry', 'Player', 'Attack-sheet')
        self.p_kick_img = import_image('Assety do gry', 'Player', 'KickPart')
        # player asset frames
        self.p_walk_frames = load_frames(self.p_walk_img, 5, 128, 128, 0.6)
        self.p_idle_frames = load_frames(self.p_idle_img, 4, 128, 128, 0.6)
        self.p_jump_frames = load_frames(self.p_jump_img, 2, 128, 128, 0.6)
        self.p_attack_frames = load_frames(self.p_attack_img, 4, 128, 128, 0.6)

        # player animation dict
        self.p_animations = {
            'idle': self.p_idle_frames,
            'walk': self.p_walk_frames,
            'jump': self.p_jump_frames,
            'attack': self.p_attack_frames,
            'kick': self.p_kick_img
        }

        # enemy assets
        self.e_idle_img = import_image('Assety do gry', 'Enemy1', 'Idle')
        self.e_jump_img = import_image('Assety do gry', 'Enemy1', 'Jump')
        self.e_attack_img = import_image('Assety do gry', 'Enemy1', 'Attack_1')
        self.e_walk_img = import_image('Assety do gry', 'Enemy1', 'Walk')
        self.e_dead_img = import_image('Assety do gry', 'Enemy1', 'Dead')
        self.e_Blood_Charge_1_img = import_image('Assety do gry', 'Enemy1', 'Blood_Charge_1')
        # enemy asset frames
        self.e_walk_frames = load_frames(self.e_walk_img, 6, 128, 128, 0.6)
        self.e_idle_frames = load_frames(self.e_idle_img, 5, 128, 128, 0.6)
        self.e_jump_frames = load_frames(self.e_jump_img, 6, 128, 128, 0.6)
        self.e_attack_frames = load_frames(self.e_attack_img, 6, 128, 128, 0.6)
        self.e_dead_frames = load_frames(self.e_dead_img, 8, 128, 128, 0.6)
        self.e_Blood_Charge_1_frames = load_frames(self.e_Blood_Charge_1_img, 3, 64, 48, 0.8)

        # enemy animation dict
        self.e_animations = {
            'idle': self.e_idle_frames,
            'walk': self.e_walk_frames,
            'jump': self.e_jump_frames,
            'attack': self.e_attack_frames,
            'dead': self.e_dead_frames,
        }

        # enemy projectile dict
        self.e_projectile = {'idle': self.e_Blood_Charge_1_frames}

        # hearts on map
        self.hp_hearts_img = import_image('Assety do gry', 'hp_hearts')
        self.hp_hearts_frames = load_frames(self.hp_hearts_img, 3, 32, 32, 1)

        # collectibles on map
        self.money_img = import_image('Assety do gry', 'Money')
        self.money_frames = load_frames(self.money_img, 6, 24, 24, 1.2)
        self.money = {'idle': self.money_frames}

    def attack_collision(self):
        """
        Ensures player attacks are colliding with the enemies
        """
        if self.player.attacking:
            for sprite in self.entities:
                if (hasattr(sprite, 'hitbox') and isinstance(sprite, Enemy) and getattr(sprite, 'can_collide', True)):
                    if self.player.attack_hitbox.colliderect(sprite.hitbox):
                        sprite.can_collide = False
                        sprite.dead = True
                        sprite.state = 'dead'
                        sprite.frame_index = 0
                        self.score += sprite.value
                        for spawn_data in self.enemy_spawn_points:
                            if sprite.hitbox.colliderect(spawn_data['rect']):
                                spawn_data['spawned'] = False
                                spawn_data['timer'] = None
                                self.start_countdown()
                                break

    def health_collision(self):
        """
        Ensures health pickups scattered around the map are being handled correctly
        """
        for hp in list(self.health_pickups):  # Use list() to safely modify during iteration
            if self.player.hitbox.colliderect(hp.rect):
                if self.player.health < self.player.max_health:  # Only collect if not at max health
                    hp.collected = True
                    self.player.health += 1
                    for spawn_data in self.heart_spawn_points:
                        if hp.rect.colliderect(spawn_data['rect']):
                            spawn_data['spawned'] = False
                            spawn_data['timer'] = None
                            break

    def collectible_collision(self):
        """
        Ensures collectibles pickups scattered around the map are being handled correctly
        """
        for money in list(self.collectibles):
            if isinstance(money, Money) and self.player.hitbox.colliderect(money.rect):
                if not money.collected:
                    money.collected = True
                    self.score += money.value
                    for spawn_data in self.collectibles_spawn_points:
                        if money.rect.colliderect(spawn_data['rect']):
                            spawn_data['spawned'] = False
                            spawn_data['timer'] = None
                            break

    def take_damage(self):
        """
        Ensures player takes damages properly from enemy attacks (projectiles)
        """
        for sprite in self.entities:
            if isinstance(sprite, Projectile):
                if self.player.hitbox.colliderect(sprite.proj_hitbox):
                    if not hasattr(sprite, 'has_damaged_player'):
                        self.player.health -= sprite.damage
                        sprite.damaged_player = True
                        if self.player.health == 0:
                            self.player_dead = True

    def create_projectile(self, pos, direction):
        """
        Creates a projectile for the enemy
        :param pos: position of the missle created - must be relatively close to enemy position
        :param direction: direction (and speed) of the projectile relative to the direction of an enemy
        """
        Projectile(self.e_projectile, pos, direction, (self.all_sprites, self.projectiles, self.entities))

    def start_countdown(self):
        """
        Countdown for the ingame timer, if it reaches zero: game over
        """
        self.countdown_time = 15
        if self.countdown_timer:
            self.countdown_timer.deactivate()
        self.countdown_timer = Timer(
            duration=1000,  # 1 second
            func=self.update_countdown,
            repeat=True,
            autostart=True
        )

    def update_countdown(self):
        """
        Handling updating the timer.
        If player dies it automatically deactivates
        """
        self.countdown_time -= 1
        if self.countdown_time <= 0:
            self.player_dead = True  # Trigger game over
            self.countdown_timer.deactivate()

    def draw_ui(self):
        """
        Drawing ui on the screen in real time
        """
        heart_size = (45, 45)
        spacing = 0
        start_pos = (0, 0)
        max_hearts = self.player.max_health

        for i in range(max_hearts):
            # full heart (frame 0) for remaining HP, grey heart (frame 2) for lost HP
            frame_index = 0 if i < self.player.health else 2
            heart_img = pygame.transform.scale(self.hp_hearts_frames[frame_index], heart_size)
            self.display_surface.blit(
                heart_img,
                (start_pos[0] + i * (heart_size[0] + spacing), start_pos[1])
            )
        score_text = f"Score: {self.score}"
        text_surface = self.font.render(score_text, True, (0, 0, 0))
        self.display_surface.blit(text_surface, (11, 41))
        text_surface = self.font.render(score_text, True, (255, 215, 0))
        self.display_surface.blit(text_surface, (10, 40))

        timer_text = f"Time: {self.countdown_time // 60}:{self.countdown_time % 60:02d}"
        if self.countdown_time >= 6:
            timer_surface = self.font.render(timer_text, True, (0, 0, 0))
            self.display_surface.blit(timer_surface, (11, 81))
            timer_surface = self.font.render(timer_text, True, (255, 215, 0))
            self.display_surface.blit(timer_surface, (10, 80))
        else:
            timer_surface = self.font.render(timer_text, True, (0, 0, 0))
            self.display_surface.blit(timer_surface, (11, 81))
            timer_surface = self.font.render(timer_text, True, (255, 0, 0))
            self.display_surface.blit(timer_surface, (10, 80))

    def setup(self):
        """
        Loading map tiles and placing the objects in the ingame world
        """
        tmx_map = load_pygame(join('Assety do gry', 'maps', 'world.tmx'))

        self.map_width = tmx_map.width * tmx_map.tilewidth * SCALE
        self.map_height = tmx_map.height * tmx_map.tileheight * SCALE
        self.map_bounds = pygame.Rect(0, 0, self.map_width, self.map_height)

        # loading tiles with collisions
        for x, y, image in tmx_map.get_layer_by_name('Main').tiles():
            scaled_image = pygame.transform.scale(image, (TILE_SIZE * SCALE, TILE_SIZE * SCALE))
            pixel_x = x * TILE_SIZE
            pixel_y = y * TILE_SIZE
            Sprite((pixel_x * SCALE, pixel_y * SCALE), scaled_image, (self.all_sprites, self.collision_sprites))
        # loading decorative assets without collisions
        for x, y, image in tmx_map.get_layer_by_name('Decorations').tiles():
            scaled_image = pygame.transform.scale(image,
                                                  (int(image.get_width() * SCALE), int(image.get_height() * SCALE)))
            pixel_x = x * TILE_SIZE * SCALE
            pixel_y = (y * TILE_SIZE * SCALE) - scaled_image.get_height() + TILE_SIZE * SCALE
            Sprite((pixel_x, pixel_y), scaled_image, (self.all_sprites))
        # loading entities such as player, enemies and pickups
        for obj in tmx_map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x * SCALE, obj.y * SCALE), (self.all_sprites, self.entities),
                                     self.collision_sprites, self.entities, self.p_animations)
                self.player_pos = obj.x
            elif obj.name == 'Enemy':
                spawn_rect = pygame.FRect(obj.x * SCALE, obj.y * SCALE, obj.width * SCALE, obj.height * SCALE)
                spawn_data = {
                    'rect': spawn_rect,
                    'spawned': True,
                    'timer': None
                }
                self.enemy_spawn_points.append(spawn_data)
                Enemy(pygame.FRect(obj.x * SCALE, obj.y * SCALE, obj.width * SCALE, obj.height * SCALE),
                      (self.all_sprites, self.entities), self.collision_sprites, self.entities, self.e_animations,
                      self.create_projectile)
            elif obj.name == 'Health':
                spawn_rect = pygame.FRect(obj.x * SCALE, obj.y * SCALE, obj.width * SCALE, obj.height * SCALE)
                spawn_data = {
                    'rect': spawn_rect,
                    'spawned': True,
                    'timer': None
                }
                self.heart_spawn_points.append(spawn_data)
                Heart((obj.x * SCALE, obj.y * SCALE),
                      self.hp_hearts_frames[0],
                      (self.all_sprites, self.entities, self.health_pickups))
            elif obj.name == 'Objective':
                spawn_rect = pygame.FRect(obj.x * SCALE, obj.y * SCALE, obj.width * SCALE, obj.height * SCALE)
                spawn_data = {
                    'rect': spawn_rect,
                    'spawned': True,
                    'timer': None,
                    'value': 100
                }
                self.collectibles_spawn_points.append(spawn_data)
                Money(self.money,
                      (obj.x * SCALE, obj.y * SCALE),
                      (self.all_sprites, self.entities, self.collectibles))
        # ensuring player bounds
        self.player.map_bounds = self.map_bounds

    def handle_respawns(self):
        """
        Respawning enemies and collectibles
        Checks for spawn areas for the entity and if there is an entity already spawned there.
        If not, it fires up a timer counting down and after that it spawns the desired entity
        """
        # enemy respawns
        for spawn_data in self.enemy_spawn_points:
            if not spawn_data['spawned']:
                if spawn_data['timer'] is None:
                    spawn_data['timer'] = Timer(
                        duration=randint(4, 18) * 1000,
                        func=lambda rect=spawn_data['rect']: self.respawn_enemy(rect),
                        repeat=False,
                        autostart=True
                    )
                if spawn_data['timer']:
                    spawn_data['timer'].update()
        # heart respawns
        for spawn_data in self.heart_spawn_points:
            if not spawn_data['spawned']:
                if spawn_data['timer'] is None:
                    spawn_data['timer'] = Timer(
                        duration=randint(8, 20) * 1000,
                        func=lambda rect=spawn_data['rect']: self.respawn_heart(rect),
                        repeat=False,
                        autostart=True
                    )
                if spawn_data['timer']:
                    spawn_data['timer'].update()

        for spawn_data in self.collectibles_spawn_points:
            if not spawn_data['spawned']:
                if spawn_data['timer'] is None:
                    spawn_data['timer'] = Timer(
                        duration=randint(10, 25) * 1000,
                        func=lambda rect=spawn_data['rect'], value=spawn_data['value']:
                        self.respawn_collectibles(rect, value),
                        repeat=False,
                        autostart=True
                    )
                if spawn_data['timer']:
                    spawn_data['timer'].update()

    def respawn_enemy(self, rect):
        """
        Creates an instance of Enemy class in the map
        :param rect: location of the entity
        """
        Enemy(rect,
              (self.all_sprites, self.entities), self.collision_sprites, self.entities, self.e_animations,
              self.create_projectile)

        for spawn_data in self.enemy_spawn_points:
            if spawn_data['rect'] == rect:
                spawn_data['spawned'] = True
                spawn_data['timer'] = None
                break

    def respawn_heart(self, rect):
        """
        Creates an instance of Heart class in the map
        :param rect: location of the entity
        """
        Heart((rect.x, rect.y),
              self.hp_hearts_frames[0],
              (self.all_sprites, self.entities, self.health_pickups))

        for spawn_data in self.heart_spawn_points:
            if spawn_data['rect'] == rect:
                spawn_data['spawned'] = True
                spawn_data['timer'] = None
                break

    def respawn_collectibles(self, rect, value):
        """
        Creates an instance of collectible Money class in the map
        :param value: value of the collectible
        :param rect: location of the entity
        """
        money = Money(self.money,
                      (rect.x, rect.y),
                      (self.all_sprites, self.entities, self.collectibles))
        money.value = value

        for spawn_data in self.collectibles_spawn_points:
            if spawn_data['rect'] == rect:
                spawn_data['spawned'] = True
                spawn_data['timer'] = None
                break

    def scroll_background(self, unupdated_x):
        """
        Handles scrolling of the dynamic 2d background
        :param unupdated_x: takes an x's old position and returns a new position to scroll the background
        """
        for x in range(5):  # times the background is redrawn
            self.speed = 1
            for i in self.bg_images:
                self.display_surface.blit(i, ((x * self.bg_width) + self.scroll * self.speed, 0))
                self.speed += 0.2

        updated_x = self.player.rect.x - unupdated_x

        updated_x = self.player.rect.x - unupdated_x
        if self.all_sprites.centered_camera:
            if updated_x < 0 and self.scroll < -5:
                self.scroll += 5
            elif updated_x > 0:
                self.scroll -= 5

    def run(self):
        """
        Main function for running the game
        """
        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000
            if not self.player_dead and not self.game_over_screen:
                unupdated_x = self.player.rect.x
                self.all_sprites.update(dt)
                self.scroll_background(unupdated_x)
                self.all_sprites.draw(self.player.rect.center, self.map_width, self.map_height)
                self.attack_collision()
                self.health_collision()
                self.collectible_collision()
                self.take_damage()
                self.draw_ui()
                self.handle_respawns()
                if self.countdown_timer:
                    self.countdown_timer.update()
            elif self.player_dead and not self.game_over_screen:
                self.game_over_screen = GameOver(self.display_surface, self.score)

            if self.game_over_screen:
                self.game_over_screen.draw()

                if self.game_over_screen and event.type == pygame.MOUSEBUTTONDOWN:
                    action = self.game_over_screen.handle_event(event)
                    if action == "restart":
                        self.__init__()
                        self.game_over_screen = None
                    elif action == "quit":
                        self.running = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            pygame.display.update()

        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
