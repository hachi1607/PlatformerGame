import pygame
from settings import *
from support import *
from timer import Timer
from random import randint
import random


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, image, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_frect(topleft=pos)
        self.map_bounds = None


class AnimatedSprite(Sprite):
    def __init__(self, animations, pos, groups):
        self.animation_speeds = {
            'idle': 5,
            'walk': 0.015 * SPEED,
            'jump': 10,
            'attack': 10
        }
        self.animations = animations  # dictionary of animation frames
        self.state = 'idle'  # animation state
        self.frame_index = 0
        self.animation_speed = 10
        self.flip = False
        super().__init__(pos, self.animations[self.state][0], groups)


class Player(AnimatedSprite):
    def __init__(self, pos, groups, collision_sprites, entities, animations):
        super().__init__(animations, pos, groups)
        self.flip = False  # player model flip flag
        self.attacking = False
        self.attack_timer = 0
        self.attack_cd = Timer(500)
        self.death_timer = Timer(1000, self.kill)
        # movement, collisions
        self.direction = pygame.Vector2()
        self.collision_sprites = collision_sprites
        self.entities = entities
        self.speed = SPEED
        self.gravity = GRAVITY
        self.on_floor = False
        self.max_health = 5
        self.health = self.max_health
        self.dead = False
        self.inputs_on = True
        self.can_collide = True

        # Create a smaller hitbox for collision
        self.hitbox = self.rect.inflate(-(self.rect.width - 20 * SCALE), -(self.rect.height - 35 * SCALE))
        self.hitbox.midbottom = self.rect.midbottom

        self.attack_hitbox = pygame.FRect(0, 0, 20 * SCALE * 2, 35 * SCALE)
        self.attack_hitbox.midleft = self.hitbox.midright

    def input(self):
        keys = pygame.key.get_pressed()
        if self.inputs_on:
            if not self.attacking:
                self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            else:
                self.direction.x = 0
            if keys[pygame.K_UP] and self.on_floor and not self.attacking:
                self.direction.y = -JUMP_HEIGHT
                self.on_floor = False
            if keys[pygame.K_SPACE] and not self.attacking and not self.attack_cd and self.on_floor:
                self.attacking = True
                self.attack_cd.activate()
                self.attack_timer = len(self.animations['attack'])
                self.frame_index = 0

    def move(self, dt):
        # update hitbox position
        self.hitbox.midbottom = self.rect.midbottom
        # horizontal
        self.hitbox.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        # vertical
        self.on_floor = False
        self.direction.y += self.gravity * dt  # acceleration increases with every frame
        self.hitbox.y += self.direction.y
        self.collision('vertical')
        # update sprite position to match hitbox
        self.rect.midbottom = self.hitbox.midbottom
        if self.flip:
            self.attack_hitbox.midright = self.hitbox.midleft
        else:
            self.attack_hitbox.midleft = self.hitbox.midright

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.hitbox.left = sprite.rect.right
                if direction == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.rect.top
                        self.on_floor = True
                    if self.direction.y < 0:
                        self.hitbox.top = sprite.rect.bottom
                    self.direction.y = 0

        if self.map_bounds:
            if direction == 'horizontal':
                if self.hitbox.left < self.map_bounds.left:
                    self.hitbox.left = self.map_bounds.left
                if self.hitbox.right > self.map_bounds.right:
                    self.hitbox.right = self.map_bounds.right

            if direction == 'vertical':
                if self.hitbox.top < self.map_bounds.top:
                    self.hitbox.top = self.map_bounds.top
                if self.hitbox.bottom > self.map_bounds.bottom:
                    self.hitbox.bottom = self.map_bounds.bottom

    def kill_player(self):
        if self.health <= 0 and not self.dead:
            self.dead = True
            self.inputs_on = False
            self.direction = pygame.Vector2()
            self.can_collide = False
            self.death_timer.activate()
            self.state = 'attack'
            self.frame_index = 0

    def animate(self, dt):
        if self.dead == True:
            self.state = 'attack'
        else:
            if self.attacking:
                self.state = 'attack'
                self.attack_timer -= dt * self.animation_speeds['attack']
                if self.attack_timer <= 0:
                    self.attacking = False
            elif self.direction.x:
                self.state = 'walk'
                self.flip = self.direction.x < 0
            else:
                self.state = 'idle'

            if not self.on_floor:
                self.state = 'jump'
                if self.direction.y < 0:
                    self.frame_index = 0
                else:
                    self.frame_index = 1

            if self.state != 'jump':
                speed = self.animation_speeds[self.state]
                self.frame_index += speed * dt

        self.image = self.animations[self.state][int(self.frame_index) % len(self.animations[self.state])]
        self.image = pygame.transform.flip(self.image, self.flip, False)

        if self.flip:
            self.attack_hitbox.midright = self.hitbox.midleft
        else:
            self.attack_hitbox.midleft = self.hitbox.midright

    def update(self, dt):
        self.kill_player()
        self.death_timer.update()
        self.attack_cd.update()
        self.input()
        self.move(dt)
        self.animate(dt)


class Enemy(AnimatedSprite):
    def __init__(self, rect, groups, collision_sprites, entities, animations, create_projectile):
        super().__init__(animations, rect.topleft, groups)
        self.create_projectile = create_projectile

        self.animation_speeds = {
            'idle': 5,
            'walk': 0.015 * SPEED,
            'jump': 10,
            'attack': 15,
            'dead': 8,
            'projectile': 7
        }
        self.rect.bottomleft = rect.bottomleft
        self.patrol_rect = rect
        self.patrol_left = rect.left
        self.patrol_right = rect.right

        if self.patrol_left >= self.patrol_right:
            self.patrol_left = rect.left
            self.patrol_right = rect.right

        self.direction = pygame.Vector2()
        self.direction.x = random.choice([-1, 1])
        self.collision_sprites = collision_sprites
        self.entities = entities
        self.speed = randint(SPEED - 200, SPEED) * 0.4
        self.gravity = GRAVITY
        self.on_floor = False
        self.flip = False
        self.dead = False

        self.value = 250

        self.all_sprites = groups[0]

        self.detection_range = 160 * SCALE
        self.player_detected = False

        self.attack_duration = Timer(len(self.animations['attack']) * randint(1,4)*100)
        self.attack_cd = Timer(randint(3,25)*100)

        self.attacking = False
        self.attack_timer = 0

        # Hitbox setup
        self.can_collide = True
        self.hitbox = self.rect.inflate(-(self.rect.width - 20 * SCALE), -(self.rect.height - 35 * SCALE))
        self.hitbox.midbottom = self.rect.midbottom

    def patrol(self):
        if self.hitbox.right >= self.patrol_right:
            self.direction.x = -1
        elif self.hitbox.left <= self.patrol_left:
            self.direction.x = 1

    def move(self, dt):
        self.patrol()
        # Update hitbox position
        self.hitbox.midbottom = self.rect.midbottom

        # Horizontal movement
        self.hitbox.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        # Vertical movement (gravity)
        self.on_floor = False
        self.direction.y += self.gravity * dt
        self.hitbox.y += self.direction.y
        self.collision('vertical')

        # Update sprite position
        self.rect.midbottom = self.hitbox.midbottom

        self.hitbox.left = max(self.patrol_left, self.hitbox.left)
        self.hitbox.right = min(self.patrol_right, self.hitbox.right)

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.rect.left
                        self.flip = False
                    if self.direction.x < 0:
                        self.hitbox.left = sprite.rect.right
                        self.flip = True
                if direction == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.rect.top
                        self.on_floor = True
                    if self.direction.y < 0:
                        self.hitbox.top = sprite.rect.bottom
                    self.direction.y = 0

        if self.map_bounds:
            if direction == 'horizontal':
                if self.hitbox.left < self.map_bounds.left:
                    self.hitbox.left = self.map_bounds.left
                if self.hitbox.right > self.map_bounds.right:
                    self.hitbox.right = self.map_bounds.right

            if direction == 'vertical':
                if self.hitbox.top < self.map_bounds.top:
                    self.hitbox.top = self.map_bounds.top
                if self.hitbox.bottom > self.map_bounds.bottom:
                    self.hitbox.bottom = self.map_bounds.bottom

    def player_detection(self):
        for entity in self.entities:
            if isinstance(entity, Player):
                # Calculate distances
                x_distance = entity.hitbox.centerx - self.hitbox.centerx
                y_distance = abs(entity.hitbox.centery - self.hitbox.centery)

                y_threshold = 50 * SCALE

                if abs(x_distance) <= self.detection_range and y_distance <= y_threshold:
                    if not self.player_detected:
                        if not hasattr(self, 'saved_direction'):
                            self.saved_direction = self.direction.x
                        self.player_detected = True
                        if not self.attacking and not self.attack_cd.active:
                            self.attack()  # Start attack
                            self.attack_cd.activate()
                    self.flip = x_distance < 0
                else:
                    if self.player_detected:
                        self.player_detected = False
                        self.direction.x = getattr(self, 'saved_direction')
                break
        if self.player_detected and not self.attacking and not self.attack_cd.active and not self.dead:
            self.attack()
            self.attack_cd.activate()

    def attack(self):
        self.attacking = True
        self.direction.x = 0
        self.attack_timer = len(self.animations['attack'])
        self.frame_index = 0

    def animate(self, dt):
        if self.dead:
            self.direction.x = 0
            speed = self.animation_speeds[self.state]
            self.frame_index += speed * dt
            if int(self.frame_index) >= len(self.animations[self.state]):
                self.kill()
        else:
            if self.attacking:
                self.state = 'attack'
                self.attack_timer -= dt * self.animation_speeds['attack']
                if self.attack_timer <= 0:
                    offset_x = 25 * SCALE  # Adjust this value as needed
                    if self.flip:
                        spawn_pos = (self.rect.midleft[0],
                                     self.rect.midleft[1] - 10 * SCALE)
                    else:  # Facing right
                        spawn_pos = (self.rect.midleft[0] + offset_x,
                                     self.rect.midright[1] - 10 * SCALE)

                    self.create_projectile(spawn_pos, -1 if self.flip else 1)
                    self.attack_cd.activate()
                    self.attacking = False
            if self.direction.x != 0:
                self.state = 'walk'
                self.flip = self.direction.x < 0
            elif self.direction.x == 0 and not self.attacking and not self.dead:
                self.state = 'idle'

            speed = self.animation_speeds[self.state]
            self.frame_index += speed * dt

        self.image = self.animations[self.state][int(self.frame_index) % len(self.animations[self.state])]
        self.image = pygame.transform.flip(self.image, self.flip, False)

    def update(self, dt):
        self.attack_cd.update()
        # print(self.state)
        self.player_detection()
        self.move(dt)
        self.animate(dt)


class Projectile(AnimatedSprite):
    def __init__(self, animation, pos, direction, groups):
        super().__init__(animation, pos, groups)
        self.animation_speed = {
            'idle': 10,
        }
        self.direction = pygame.Vector2()
        self.direction.x = direction
        self.speed = SPEED * 1.1
        self.flip = False
        self.damage = 1
        self.damaged_player = False

        self.hitbox_offset = 10 * SCALE
        self.proj_hitbox = self.rect.inflate(-(self.rect.width - 18 * SCALE), -(self.rect.height - 18 * SCALE))
        self.rect.center = self.proj_hitbox.center
        self.kill_proj = Timer(1500, self.kill, autostart=True)

    def animate(self, dt):
        speed = self.animation_speed['idle']
        self.frame_index += speed * dt

        self.image = self.animations['idle'][int(self.frame_index) % len(self.animations['idle'])]
        self.image = pygame.transform.flip(self.image, self.flip, False)

    def move(self, dt):
        self.rect.x += self.direction.x * self.speed * dt
        self.flip = self.direction.x < 0  # Set flip based on direction

        if self.direction.x > 0:  # Facing right
            self.proj_hitbox.midleft = self.rect.midleft
            self.proj_hitbox.x += self.hitbox_offset
        else:  # Facing left
            self.proj_hitbox.midright = self.rect.midright
            self.proj_hitbox.x -= self.hitbox_offset
        if self.damaged_player:
            self.kill()

    def update(self, dt):
        self.kill_proj.update()
        self.move(dt)
        self.animate(dt)


class Heart(Sprite):
    def __init__(self, pos, image, groups):
        super().__init__(pos, image, groups)
        self.collected = False

    def update(self, dt):
        if self.collected:
            self.kill()


class Money(AnimatedSprite):
    def __init__(self, animations, pos, groups):
        super().__init__(animations, pos, groups)
        self.collected = False
        self.animation_speed = {
            'idle': 10,
        }
        self.value = 100

    def animate(self, dt):
        speed = self.animation_speed['idle']
        self.frame_index += speed * dt

        self.image = self.animations['idle'][int(self.frame_index) % len(self.animations['idle'])]
        self.image = pygame.transform.flip(self.image, self.flip, False)

    def update(self, dt):
        self.animate(dt)
        if self.collected:
            self.kill()