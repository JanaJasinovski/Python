import pygame
import random
import sys

FRAMERATE = 10
SEGMENT_WIDTH = 20
SEGMENT_HEIGHT = 20
SEGMENT_MARGIN = 5
WALL_THICKNESS = 25
BUTTON_PADX = 50
BUTTON_PADY = 2

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (95, 135, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
DARK_GREEN = (0, 200, 0)
DARK_BLUE = (65, 105, 225)
YELLOW = (255, 255, 0)
DARK_RED = (200, 0, 0)
GREY = (211, 211, 211)

DEFAULT_FONT = 'freesansbold.ttf'


class Button:
    def __init__(self, screen, font, text, text_color, color, centerx, centery):
        self.font = font
        self.text_color = text_color
        self.text = text
        self.button_text = self.font.render(self.text, True, self.text_color)
        self.button_text_pos = self.button_text.get_rect()
        self.button_text_pos.center = (centerx, centery)
        self.screen = screen
        self.button_color = color
        self.color = color
        self.clicked = False

    def add_paddings(self, padx=0, pady=0):
        self.button_rect = self.button_text_pos.inflate(padx, pady)

    def draw(self):
        pygame.draw.rect(self.screen, self.button_color, self.button_rect)
        self.screen.blit(self.button_text, self.button_text_pos)
        self.clicked = False

    def mouse_handler(self, mouse_pos, mouse_state, hover=False, hover_color=None, on_click=None):
        self.clicked = False
        if self.button_rect.collidepoint(mouse_pos):
            if hover:
                self.button_color = hover_color
            if on_click and any(mouse_state):
                self.clicked = True
                on_click()
        else:
            self.button_color = self.color


class ToggleButton(Button):

    def __init__(self, default=True, *args, **kwargs):
        self.status = default
        self.toggle_text = False
        super().__init__(*args, **kwargs)

    def set_toggle(self, true_text, true_color, state=True):
        self.toggle_text = state
        self.true_text = true_text
        self.true_color = true_color

    def draw(self):
        if self.toggle_text:
            if self.status:
                self.button_color = self.true_color
                self.button_text = self.font.render(self.true_text, True, self.text_color)
        super().draw()

    def mouse_handler(self, *args, **kwargs):
        super().mouse_handler(*args, **kwargs)
        if self.clicked:
            self.status = not self.status


class Snake(pygame.sprite.Group):

    def __init__(self, start_x, start_y, length=2):
        super().__init__()
        self.start_x = start_x
        self.start_y = start_y
        self.length = length
        self.snake_segments = []
        self.segment_width = SEGMENT_WIDTH
        self.segment_height = SEGMENT_HEIGHT
        self.segment_margin = SEGMENT_MARGIN
        self.last_removed = None

        self.segment_size = self.segment_width + self.segment_margin

        for i in range(self.length):
            x = self.start_x - (self.segment_size) * i
            y = self.start_y
            self.add_segment(x, y)

        self.x_vel = 1 * self.segment_size
        self.y_vel = 0

    def add_segment(self, x, y, index=None):
        if index is None:
            index = self.length
        segment = SnakeSegment(x, y, self.segment_width, self.segment_height)
        self.snake_segments.insert(index, segment)
        self.add(segment)
        self.length += 1

    def pop(self):
        last_segment = self.snake_segments.pop()
        self.last_removed = last_segment
        self.remove(last_segment)
        self.length -= 1

    def head(self):
        return self.snake_segments[0]

    def tail(self):
        return self.snake_segments[1:]

    def on_horizontal(self):
        return self.y_vel == 0

    def on_vertical(self):
        return self.x_vel == 0

    def go_left(self):
        self.x_vel = -1 * (self.segment_size)
        self.y_vel = 0

    def go_right(self):
        self.x_vel = 1 * (self.segment_size)
        self.y_vel = 0

    def go_up(self):
        self.x_vel = 0
        self.y_vel = -1 * (self.segment_size)

    def go_down(self):
        self.x_vel = 0
        self.y_vel = 1 * (self.segment_size)

    def move(self, bound):
        self.pop()

        x = self.head().x + self.x_vel
        if x > bound['max_x']:
            x = bound['min_x'] + SEGMENT_MARGIN
        elif x < bound['min_x']:
            x = bound['max_x'] + SEGMENT_MARGIN
        y = self.head().y + self.y_vel
        if y > bound['max_y']:
            y = bound['min_y'] + SEGMENT_MARGIN
        elif y < bound['min_y']:
            y = bound['max_y'] + SEGMENT_MARGIN
        self.add_segment(x, y, 0)

    def collides(self, sprite1):
        return self.head().check_collision(sprite1)

    def collides_any(self, group):
        for sprite in group:
            if self.collides(sprite):
                return True
        return False

    def grow(self):
        self.add_segment(self.last_removed.rect.x, self.last_removed.rect.y)


class SnakeSegment(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height):
        super().__init__()

        self.x = x
        self.y = y

        self.image = pygame.Surface([width, height])
        self.image.fill(DARK_GREEN)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def check_collision(self, sprite1):
        return pygame.sprite.collide_rect(self, sprite1)


class Wall(pygame.sprite.Sprite):

    def __init__(self, color, startpoint, endpoint, thickness):
        super().__init__()
        width = abs(endpoint[0] - startpoint[0])
        height = abs(endpoint[1] - startpoint[1])
        if width == 0:
            width = thickness
        if height == 0:
            height = thickness

        self.image = pygame.Surface([width, height])
        self.image.fill(color)

        self.rect = self.image.get_rect()
        self.rect.x = startpoint[0]
        self.rect.y = startpoint[1]


class Food(pygame.sprite.Sprite):

    def __init__(self, x_bound, y_bound):
        super().__init__()

        self.image = pygame.Surface([SEGMENT_WIDTH, SEGMENT_HEIGHT])
        self.image.fill(RED)

        self.rect = self.image.get_rect()
        self.x_bound = x_bound
        self.y_bound = y_bound

    def spawn(self):
        segmentx_size = SEGMENT_WIDTH + SEGMENT_MARGIN
        segmenty_size = SEGMENT_HEIGHT + SEGMENT_MARGIN
        randx = random.randint(self.x_bound[0] // segmentx_size, self.x_bound[1] // segmentx_size - 1)
        randy = random.randint(self.y_bound[0] // segmenty_size, self.y_bound[1] // segmenty_size - 1)
        self.rect.x = (randx - 1) * segmentx_size + SEGMENT_MARGIN + WALL_THICKNESS
        self.rect.y = (randy - 1) * segmenty_size + SEGMENT_MARGIN + WALL_THICKNESS

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Mistake(pygame.sprite.Sprite):

    def __init__(self, x_bound, y_bound):
        super().__init__()

        self.image = pygame.Surface([SEGMENT_WIDTH, SEGMENT_HEIGHT])
        self.image.fill(BLUE)

        self.rect = self.image.get_rect()
        self.x_bound = x_bound
        self.y_bound = y_bound

    def spawn(self):
        segmentx_size = SEGMENT_WIDTH + SEGMENT_MARGIN
        segmenty_size = SEGMENT_HEIGHT + SEGMENT_MARGIN
        randx = random.randint(self.x_bound[0] // segmentx_size, self.x_bound[1] // segmentx_size - 1)
        randy = random.randint(self.y_bound[0] // segmenty_size, self.y_bound[1] // segmenty_size - 1)
        self.rect.x = (randx - 1) * segmentx_size + SEGMENT_MARGIN + WALL_THICKNESS
        self.rect.y = (randy - 1) * segmenty_size + SEGMENT_MARGIN + WALL_THICKNESS

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Ob(pygame.sprite.Sprite):

    def __init__(self, x_bound, y_bound):
        super().__init__()

        self.image = pygame.Surface([SEGMENT_WIDTH, SEGMENT_HEIGHT])
        self.image.fill(YELLOW)

        self.rect = self.image.get_rect()
        self.x_bound = x_bound
        self.y_bound = y_bound

    def spawn(self):
        segmentx_size = SEGMENT_WIDTH + SEGMENT_MARGIN
        segmenty_size = SEGMENT_HEIGHT + SEGMENT_MARGIN
        randx = random.randint(self.x_bound[0] // segmentx_size, self.x_bound[1] // segmentx_size - 1)
        randy = random.randint(self.y_bound[0] // segmenty_size, self.y_bound[1] // segmenty_size - 1)
        self.rect.x = (randx - 1) * segmentx_size + SEGMENT_MARGIN + WALL_THICKNESS
        self.rect.y = (randy - 1) * segmenty_size + SEGMENT_MARGIN + WALL_THICKNESS

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class App:

    def __init__(self, width=800, height=600):
        pygame.mixer.init()
        pygame.init()
        pygame.font.init()
        self.screen_width = width
        self.screen_height = height
        self.screen = pygame.display.set_mode([self.screen_width, self.screen_height])
        pygame.display.set_caption('Змейка')
        self.font = pygame.font.Font(DEFAULT_FONT, 60)
        self.small_font = pygame.font.Font(DEFAULT_FONT, 40)

        self.walls_toggle = True
        self.toggle_font = pygame.font.Font(DEFAULT_FONT, 40)

        self.clock = pygame.time.Clock()

    def game_init(self):
        self.score = 0
        self.running = True

        self.score_board = pygame.Surface((self.screen_width, 100))
        self.score_text = self.font.render("Счёт: " + str(self.score), True, RED)
        self.score_text_pos = self.score_text.get_rect()
        self.score_text_pos.centerx = self.score_board.get_rect().centerx
        self.score_text_pos.centery = self.score_board.get_rect().centery

        self.game_bound = {
            'min_x': 0,
            'max_x': self.screen_width,
            'min_y': 100,
            'max_y': self.screen_height,
        }

        if self.walls_toggle:
            wall_color = YELLOW
            wall_list = [
                Wall(wall_color, (self.game_bound['min_x'], self.game_bound['min_y']),
                     (self.game_bound['max_x'], self.game_bound['min_y']), WALL_THICKNESS),
                Wall(wall_color, (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['min_y']),
                     (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['max_y']), WALL_THICKNESS),
                Wall(wall_color, (self.game_bound['min_x'], self.game_bound['max_y'] - WALL_THICKNESS),
                     (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS),
                     WALL_THICKNESS),
                Wall(wall_color, (self.game_bound['min_x'], self.game_bound['min_y']),
                     (self.game_bound['min_x'], self.game_bound['max_y']), WALL_THICKNESS)
            ]
            self.walls = pygame.sprite.Group()
            self.walls.add(wall_list)

        self.food = Food((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                         (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.food.spawn()

        self.mistake = Mistake((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                               (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.mistake.spawn()

        self.ob1 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob1.spawn()
        self.ob2 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob2.spawn()
        self.ob3 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob3.spawn()
        self.ob4 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob4.spawn()
        self.ob5 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob5.spawn()
        self.ob6 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob6.spawn()
        self.ob7 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob7.spawn()
        self.ob8 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob8.spawn()
        self.ob9 = Ob((self.game_bound['min_x'] + WALL_THICKNESS, self.game_bound['max_x'] - WALL_THICKNESS),
                      (self.game_bound['min_y'] + WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS))
        self.ob9.spawn()

        self.snake = Snake(self.game_bound['min_x'] + WALL_THICKNESS + SEGMENT_MARGIN,
                           self.game_bound['min_y'] + WALL_THICKNESS + SEGMENT_MARGIN)

    def run(self):
        self.game_init()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.on_pause()
                    if self.snake.on_vertical():
                        if event.key == pygame.K_LEFT:
                            self.snake.go_left()
                        elif event.key == pygame.K_RIGHT:
                            self.snake.go_right()
                    elif self.snake.on_horizontal():
                        if event.key == pygame.K_UP:
                            self.snake.go_up()
                        elif event.key == pygame.K_DOWN:
                            self.snake.go_down()

            self.screen.fill(WHITE)
            self.score_board.fill(GREY)

            self.score_text = self.font.render("Счёт: " + str(self.score), True, RED)

            self.snake.move(self.game_bound)
            if self.walls_toggle:
                self.walls.draw(self.screen)

            self.food.draw(self.screen)
            self.mistake.draw(self.screen)
            self.ob1.draw(self.screen)
            self.ob2.draw(self.screen)
            self.ob3.draw(self.screen)
            self.ob4.draw(self.screen)
            self.ob5.draw(self.screen)
            self.ob6.draw(self.screen)
            self.ob7.draw(self.screen)
            self.ob8.draw(self.screen)
            self.ob9.draw(self.screen)

            self.snake.draw(self.screen)
            self.score_board.blit(self.score_text, self.score_text_pos)

            pygame.draw.rect(self.screen, GREEN, self.snake.head().rect, 1)

            if self.walls_toggle:
                if self.snake.collides_any(self.walls) or self.snake.collides_any(
                        self.snake.tail() or self.snake.collides(self.ob1)):
                    self.running = False
                    self.game_end()
                elif self.snake.collides_any(self.snake.tail()):
                    self.running = False
                    self.game_end()
                else:
                    if self.snake.collides(self.ob1) or self.snake.collides(self.ob2) or self.snake.collides(self.ob2) \
                            or self.snake.collides(self.ob3) or self.snake.collides(self.ob4) or self.snake.collides(
                        self.ob5) \
                            or self.snake.collides(self.ob6) or self.snake.collides(self.ob7) or self.snake.collides(
                        self.ob8) \
                            or self.snake.collides(self.ob9):
                        self.running = False
                        self.game_end()

            if self.snake.collides(self.food):
                self.food.image.fill(RED)
                self.score += 1
                self.snake.grow()
                self.food.spawn()
                if self.walls_toggle:
                    wall_color = RED
                    wall_list = [
                        Wall(wall_color, (self.game_bound['min_x'], self.game_bound['min_y']),
                             (self.game_bound['max_x'], self.game_bound['min_y']), WALL_THICKNESS),
                        Wall(wall_color, (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['min_y']),
                             (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['max_y']), WALL_THICKNESS),
                        Wall(wall_color, (self.game_bound['min_x'], self.game_bound['max_y'] - WALL_THICKNESS),
                             (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS),
                             WALL_THICKNESS),
                        Wall(wall_color, (self.game_bound['min_x'], self.game_bound['min_y']),
                             (self.game_bound['min_x'], self.game_bound['max_y']), WALL_THICKNESS)
                    ]
                    self.walls = pygame.sprite.Group()
                    self.walls.add(wall_list)

            if self.snake.collides(self.mistake):
                self.food.image.fill(BLUE)

                if self.walls_toggle:
                    wall_color = BLUE
                    wall_list = [
                        Wall(wall_color, (self.game_bound['min_x'], self.game_bound['min_y']),
                             (self.game_bound['max_x'], self.game_bound['min_y']), WALL_THICKNESS),
                        Wall(wall_color, (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['min_y']),
                             (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['max_y']), WALL_THICKNESS),
                        Wall(wall_color, (self.game_bound['min_x'], self.game_bound['max_y'] - WALL_THICKNESS),
                             (self.game_bound['max_x'] - WALL_THICKNESS, self.game_bound['max_y'] - WALL_THICKNESS),
                             WALL_THICKNESS),
                        Wall(wall_color, (self.game_bound['min_x'], self.game_bound['min_y']),
                             (self.game_bound['min_x'], self.game_bound['max_y']), WALL_THICKNESS)
                    ]
                    self.walls = pygame.sprite.Group()
                    self.walls.add(wall_list)

            self.screen.blit(self.score_board, (0, 0))
            pygame.display.update()
            self.clock.tick(FRAMERATE)

    def main_menu(self):
        self.intro_text = self.font.render("Змейка", True, BLACK)
        self.intro_text_pos = self.intro_text.get_rect()
        self.intro_text_pos.center = ((self.screen_width / 2), (self.screen_height / 4))

        start_button = Button(
            self.screen, self.font, "Начать игру",
            BLACK, DARK_GREEN, self.intro_text_pos.centerx,
            self.intro_text_pos.centery + 200
        )
        start_button.add_paddings(BUTTON_PADX, BUTTON_PADY)

        quit_button = Button(
            self.screen, self.font, "Покинуть игру",
            BLACK, DARK_RED, self.intro_text_pos.centerx,
            self.intro_text_pos.centery + 350
        )
        quit_button.add_paddings(BUTTON_PADX, BUTTON_PADY)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()

            self.screen.fill(WHITE)


            mouse_pos = pygame.mouse.get_pos()
            mouse_click = pygame.mouse.get_pressed()

            start_button.mouse_handler(mouse_pos, [mouse_click[0]], True, GREEN, self.run)
            quit_button.mouse_handler(mouse_pos, [mouse_click[0]], True, RED, self.quit)

            def walls_switch():
                self.walls_toggle = not self.walls_toggle

            self.screen.blit(self.intro_text, self.intro_text_pos)

            start_button.draw()
            quit_button.draw()

            pygame.display.update()
            self.clock.tick(FRAMERATE)

    def game_end(self):
        self.endgame_text = self.font.render("Игра окончена! Счёт {}".format(self.score), True, BLACK)
        self.endgame_text_pos = self.endgame_text.get_rect()
        self.endgame_text_pos.center = ((self.screen_width / 2), (self.screen_height / 4))

        try_again_button = Button(
            self.screen, self.font, "Поробывать ещё раз",
            BLACK, DARK_GREEN, self.endgame_text_pos.centerx,
            self.endgame_text_pos.centery + 150
        )
        try_again_button.add_paddings(BUTTON_PADX, BUTTON_PADY)

        quit_button = Button(
            self.screen, self.font, "Покинуть игру",
            BLACK, DARK_RED, self.endgame_text_pos.centerx,
            self.endgame_text_pos.centery + 350
        )
        quit_button.add_paddings(BUTTON_PADX, BUTTON_PADY)

        back_menu_button = Button(
            self.screen, self.font, "На главное меню",
            BLACK, DARK_BLUE, self.endgame_text_pos.centerx,
            self.endgame_text_pos.centery + 250
        )
        back_menu_button.add_paddings(BUTTON_PADX, BUTTON_PADY)

        end = True
        while end:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()

            self.screen.fill(WHITE)

            mouse_pos = pygame.mouse.get_pos()
            mouse_click = pygame.mouse.get_pressed()

            try_again_button.mouse_handler(mouse_pos, [mouse_click[0]], True, GREEN, self.run)
            back_menu_button.mouse_handler(mouse_pos, [mouse_click[0]], True, BLUE, self.main_menu)
            quit_button.mouse_handler(mouse_pos, [mouse_click[0]], True, RED, self.quit)

            self.screen.blit(self.endgame_text, self.endgame_text_pos)

            try_again_button.draw()
            back_menu_button.draw()
            quit_button.draw()

            pygame.display.update()
            self.clock.tick(FRAMERATE)

    def quit(self):
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    snake_app = App()
    snake_app.main_menu()
