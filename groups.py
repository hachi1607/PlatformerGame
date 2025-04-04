from settings import *
from sprites import Player, Enemy

class AllSprites(pygame.sprite.Group):
    '''
    Handles proper displaying of all sprites from all groups properly on the display
    '''
    def __init__(self):
        """
        Calls games surface to draw sprites on
        """
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()
        self.centered_camera = False

    def draw(self, target_pos, map_width, map_height):
        # centered camera following the player at all times,
        # but stopping at map's edges
        desired_offset_x = -(target_pos[0] - WINDOW_WIDTH / 2)
        desired_offset_y = -(target_pos[1] - WINDOW_HEIGHT / 2)

        self.offset.x = max(-(map_width - WINDOW_WIDTH), min(0, desired_offset_x))
        self.offset.y = max(-(map_height - WINDOW_HEIGHT), min(0, desired_offset_y))

        self.centered_camera = (
                desired_offset_x >= -(map_width - WINDOW_WIDTH) and
                desired_offset_x <= 0
        )

        # ensuring player model is always at the top
        player_sprite = None

        for sprite in self:
            if isinstance(sprite, Player):
                player_sprite = sprite
            else:
                offset_pos = sprite.rect.topleft + self.offset
                self.display_surface.blit(sprite.image, offset_pos)

                # debugging htiboxes
            # if hasattr(sprite, 'attack_hitbox'):
            #     pygame.draw.rect(self.display_surface, (0, 255, 255), sprite.attack_hitbox.move(self.offset), 2)
            # self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)
            # if hasattr(sprite, 'hitbox'):
            #     pygame.draw.rect(self.display_surface, (255, 0, 0), sprite.hitbox.move(self.offset), 2)
            # if hasattr(sprite, 'proj_hitbox'):
            #     pygame.draw.rect(self.display_surface, (0, 255, 0), sprite.proj_hitbox.move(self.offset), 2)

        if player_sprite:
            offset_pos = player_sprite.rect.topleft + self.offset
            self.display_surface.blit(player_sprite.image, offset_pos)

            # kick image render
            if player_sprite.attacking:
                kick_img = player_sprite.animations['kick']
                kick_img = pygame.transform.scale(player_sprite.animations['kick'], (
                int(kick_img.get_width() * SCALE * 0.6), int(kick_img.get_height() * SCALE * 0.6)))
                if player_sprite.flip:
                    kick_img = pygame.transform.flip(kick_img, True, False)
                    kick_rect = kick_img.get_rect(left=player_sprite.attack_hitbox.left, centery=player_sprite.attack_hitbox.centery - 15
                    )
                else:
                    kick_rect = kick_img.get_rect(right=player_sprite.attack_hitbox.right, centery=player_sprite.attack_hitbox.centery - 15)
                self.display_surface.blit(kick_img, kick_rect.topleft + self.offset)