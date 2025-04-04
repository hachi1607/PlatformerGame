import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, SCALE


class GameOver:
    def __init__(self, display_surface, score):
        self.display_surface = display_surface
        self.score = score
        self.active = False

        self.title_font = pygame.font.Font('dogicapixel.ttf', 72)
        self.text_font = pygame.font.Font('dogicapixel.ttf', 36)

        self.title_color = (200, 0, 0)
        self.text_color = (255, 255, 255)
        self.shadow_color = (0, 0, 0)

        self.buttons = [
            {"text": "Restart", "rect": pygame.Rect(0, 0, 300, 75), "action": "restart"},
            {"text": "Quit", "rect": pygame.Rect(0, 0, 300, 75), "action": "quit"}
        ]

        self._position_elements()

    def _position_elements(self):
        total_height = len(self.buttons) * (self.buttons[0]["rect"].height + 0)
        start_y = (WINDOW_HEIGHT - total_height) // 2 + 50 * SCALE

        for i, button in enumerate(self.buttons):
            button["rect"].centerx = WINDOW_WIDTH // 2
            button["rect"].y = start_y + i * (button["rect"].height + 5)

    def draw(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.display_surface.blit(overlay, (0, 0))

        title_text = self.title_font.render("GAME OVER", True, self.title_color)
        title_shadow = self.title_font.render("GAME OVER", True, self.shadow_color)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))

        self.display_surface.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        self.display_surface.blit(title_text, title_rect)

        score_text = self.text_font.render(f"Final Score: {self.score}", True, self.text_color)
        score_shadow = self.text_font.render(f"Final Score: {self.score}", True, self.shadow_color)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, title_rect.bottom + 20 * SCALE))

        self.display_surface.blit(score_shadow, (score_rect.x + 2, score_rect.y + 2))
        self.display_surface.blit(score_text, score_rect)

        for button in self.buttons:
            pygame.draw.rect(self.display_surface, (70, 70, 70), button["rect"])
            pygame.draw.rect(self.display_surface, (100, 100, 100), button["rect"], 3)

            text = self.text_font.render(button["text"], True, self.text_color)
            text_shadow = self.text_font.render(button["text"], True, self.shadow_color)
            text_rect = text.get_rect(center=button["rect"].center)

            self.display_surface.blit(text_shadow, (text_rect.x + 1, text_rect.y + 1))
            self.display_surface.blit(text, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button["rect"].collidepoint(event.pos):
                    return button["action"]
        return None
