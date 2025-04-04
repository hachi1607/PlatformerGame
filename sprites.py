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
        # different animation speed for every state
        self.animation_speeds = {
            'idle': 5,
            'walk': 0.015 * SPEED,
            'jump': 10,
            'attack': 10
        }
        self.animations = animations  # dictionary of animation frames
        self.state = 'idle'  # default animation state
        self.frame_index = 0
        self.animation_speed = 10
        self.flip = False
        super().__init__(pos, self.animations[self.state][0], groups)


class Player(AnimatedSprite):
    def __init__(self, pos, groups, collision_sprites, entities, animations):
        super().__init__(animations, pos, groups)
        self.flip = False  # player model flip flag
        self.attacking = False # boolean flag if player is currently attacking
        self.attack_timer = 0 # counts the time of the whole attack
        self.attack_cd = Timer(500) # cooldown between the attacks
        # self.death_timer = Timer(1000, self.kill) # scratched concept

        # movement, collisions
        self.direction = pygame.Vector2() # current direction
        self.collision_sprites = collision_sprites # collision spirtes such as terrain
        self.entities = entities # entites such as enemies or collectibles
        self.speed = SPEED # current player speed
        self.gravity = GRAVITY # gravity force
        self.on_floor = False # checks if player is currently on the floor
        self.max_health = 4 # player max hp
        self.health = self.max_health # set current health at initializing at max health
        self.dead = False # checks if player died
        # self.inputs_on = True
        # self.can_collide = True

        # Create a smaller hitbox rect for collision (smaller than texture rect)
        self.hitbox = self.rect.inflate(-(self.rect.width - 20 * SCALE), -(self.rect.height - 35 * SCALE))
        self.hitbox.midbottom = self.rect.midbottom

        # Attack hitbox for the kick
        self.attack_hitbox = pygame.FRect(0, 0, 20 * SCALE * 2, 35 * SCALE)
        self.attack_hitbox.midleft = self.hitbox.midright

    def input(self):
        """
        Player key input handling
        """
        keys = pygame.key.get_pressed()
        if not self.attacking:
            # simple calculations of subraction for the direction vector
            self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        else:
            self.direction.x = 0
        if keys[pygame.K_UP] and self.on_floor and not self.attacking:
            # negative y vector, so player goes up
            self.direction.y = -JUMP_HEIGHT
            self.on_floor = False
        if keys[pygame.K_SPACE] and not self.attacking and not self.attack_cd and self.on_floor:
            self.attacking = True
            self.attack_cd.activate()
            self.attack_timer = len(self.animations['attack'])
            self.frame_index = 0

    def move(self, dt):
        """
        Movement and gravity handling
        :param dt: deltatime (subticks) for precise location calculations between frames
        """
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
        """
        Handling terrain colisions with player
        :param direction: current direction
        """
        # hitbox collisions with terrain
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

        # setting map boundaries to not let the player fall off
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
            self.direction = pygame.Vector2()
            self.can_collide = False
            # self.death_timer.activate()
            # self.frame_index = 0
            # self.inputs_on = False

    def animate(self, dt):
        """
        Displaying proper animation frames for each state with certain speed
        set in the dictionairy of the class

        :param dt: deltatime
        """
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
        # animation frames flip in case of flipping player
        self.image = pygame.transform.flip(self.image, self.flip, False)

        if self.flip:
            self.attack_hitbox.midright = self.hitbox.midleft
        else:
            self.attack_hitbox.midleft = self.hitbox.midright

    def update(self, dt):
        """
        Live updating and tracking behaviour of the player
        :param dt: deltatime
        """
        self.kill_player()
        # self.death_timer.update()
        self.attack_cd.update()
        self.input()
        self.move(dt)
        self.animate(dt)


class Enemy(AnimatedSprite):
    def __init__(self, rect, groups, collision_sprites, entities, animations, create_projectile):
        super().__init__(animations, rect.topleft, groups)
        self.create_projectile = create_projectile #calling creating projectile if conditions met

        # animations speed for each state
        self.animation_speeds = {
            'idle': 5,
            'walk': 0.015 * SPEED,
            'jump': 10,
            'attack': 15,
            'dead': 8,
            'projectile': 7
        }
        # enemy rect position
        self.rect.bottomleft = rect.bottomleft
        self.patrol_rect = rect # patrol rect for tracking enemy are bounds
        self.patrol_left = rect.left
        self.patrol_right = rect.right

        # not sure if it's neccessary at this point
        if self.patrol_left >= self.patrol_right:
            self.patrol_left = rect.left
            self.patrol_right = rect.right

        self.direction = pygame.Vector2() # direction vector
        self.direction.x = random.choice([-1, 1]) # random direction when spawning in
        self.collision_sprites = collision_sprites # groups passed in
        self.entities = entities
        self.speed = randint(SPEED - 200, SPEED) * 0.4 # random speed for every instance of an enemy
        self.gravity = GRAVITY # gravity from settings
        self.on_floor = False # check if enemy on floor (not neccessary)
        self.flip = False # enemy flip flag
        self.dead = False # chceck if the enemy is dead flag

        self.value = 250 # point value for killing the enemy

        self.all_sprites = groups[0] # all sprites group passed in

        self.detection_range = 160 * SCALE # player detection range
        self.player_detected = False # if player detected flag
        self.attack_cd = Timer(randint(3,25)*100) # random attack cooldown

        self.attacking = False # check if enemy is attacking flag
        self.attack_timer = 0  # attack speed duration counter

        # Hitbox setup
        self.can_collide = True
        self.hitbox = self.rect.inflate(-(self.rect.width - 20 * SCALE), -(self.rect.height - 35 * SCALE))
        self.hitbox.midbottom = self.rect.midbottom

    def patrol(self):
        """
        Change walking direction if Enemy entity box bounds met with hitbox
        """
        if self.hitbox.right >= self.patrol_right:
            self.direction.x = -1
        elif self.hitbox.left <= self.patrol_left:
            self.direction.x = 1

    def move(self, dt):
        """
        Enemy moving mechanic
        :param dt:
        """
        self.patrol() # patroling as default behaviour
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
        """
        Collision handling
        :param direction: direction vector passed in
        """
        # terrain colision handling
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
        # map bounds handling to not let the enemy fall out
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
        """
        Player detection logic handling
        """
        for entity in self.entities:
            if isinstance(entity, Player):
                # Calculate distances
                x_distance = entity.hitbox.centerx - self.hitbox.centerx
                y_distance = abs(entity.hitbox.centery - self.hitbox.centery)

                y_threshold = 50 * SCALE # distance for player to be spotted

                # if x distance of the player smaller than detection range, detect player
                if abs(x_distance) <= self.detection_range and y_distance <= y_threshold:
                    if not self.player_detected: # if the flag is not set yet:
                        if not hasattr(self, 'saved_direction'): # save movement direction if player leave detection zone
                            self.saved_direction = self.direction.x
                        self.player_detected = True # then set detection flag true
                        if not self.attacking and not self.attack_cd.active:
                            self.attack()  # start attack
                            self.attack_cd.activate() # cooldown
                    self.flip = x_distance < 0 # flipping enemy model based on direction
                else: # if player not in detection range:
                    if self.player_detected:
                        self.player_detected = False # set detection flag to false
                        self.direction.x = getattr(self, 'saved_direction')
                break
        # continue attacking after spotting and finishing first attack cycle
        if self.player_detected and not self.attacking and not self.attack_cd.active and not self.dead:
            self.attack()
            self.attack_cd.activate()

    def attack(self):
        # stop enemey and reset attack animation frames for each attack cycle
        self.attacking = True
        self.direction.x = 0
        self.attack_timer = len(self.animations['attack'])
        self.frame_index = 0

    def animate(self, dt):
        """
        Enemey animation handling for each state
        :param dt: deltatime
        """
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
                    offset_x = 25 * SCALE
                    if self.flip:
                        spawn_pos = (self.rect.midleft[0],
                                     self.rect.midleft[1] - 10 * SCALE)
                    else:  # Facing right
                        spawn_pos = (self.rect.midleft[0] + offset_x,
                                     self.rect.midright[1] - 10 * SCALE)
                    # create projectile entity for each attack cycle
                    self.create_projectile(spawn_pos, -1 if self.flip else 1)
                    self.attack_cd.activate() # activate attack cd
                    self.attacking = False # not attacking so no attack animation frames in between cooldown
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
        self.speed = SPEED * 1.1 # projectile speed
        self.flip = False
        self.damage = 1 # projectile damage
        self.damaged_player = False

        self.hitbox_offset = 10 * SCALE
        self.proj_hitbox = self.rect.inflate(-(self.rect.width - 18 * SCALE), -(self.rect.height - 18 * SCALE))
        self.rect.center = self.proj_hitbox.center
        self.kill_proj = Timer(1500, self.kill, autostart=True) # deleting projectile after it flew given distance

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