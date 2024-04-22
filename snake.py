import json
import random

class Cube:
    def __init__(self, start, color=(255, 0, 0)):
        self.pos = start
        self.color = color

class Snake:
    def __init__(self, color, pos):
        self.color = color
        self.head = Cube(pos, color=color)
        self.body = [self.head]
        self.turns = {}
        self.dirnx, self.dirny = 0, 1  # Initial direction: down

    def move(self):
        for i, c in enumerate(self.body):
            p = c.pos[:]
            if p in self.turns:
                turn = self.turns[p]
                self.dirnx, self.dirny = turn
                c.pos = (p[0] + self.dirnx, p[1] + self.dirny)
                if i == len(self.body) - 1:
                    self.turns.pop(p)
            else:
                c.pos = (p[0] + self.dirnx, p[1] + self.dirny)

    def reset(self, pos):
        self.head = Cube(pos, color=self.color)
        self.body = [self.head]
        self.turns = {}
        self.dirnx, self.dirny = 0, 1

    def add_cube(self):
        tail = self.body[-1]
        new_pos = tail.pos  # Default to tail's position

        # Determine the new position based on the second-last cube's position
        if len(self.body) > 1:
            second_last_cube = self.body[-2]
            new_pos = (tail.pos[0] + (tail.pos[0] - second_last_cube.pos[0]),
                       tail.pos[1] + (tail.pos[1] - second_last_cube.pos[1]))
        else:
            # If the snake has only one cube, use the head's current direction
            new_pos = (tail.pos[0] - self.dirnx, tail.pos[1] - self.dirny)

        self.body.append(Cube(new_pos, self.color))

    def get_positions(self):
        return [c.pos for c in self.body]

    def get_head_position(self):
        return self.head.pos

class SnakeGame:
    def __init__(self, rows):
        self.rows = rows
        self.players = {}
        self.snacks = [self.random_snack() for _ in range(5)]

    def add_player(self, user_id):
        start_pos = (random.randint(1, self.rows - 1), random.randint(1, self.rows - 1))
        color = self.generate_unique_color()  # Generate a unique color
        self.players[user_id] = Snake(color, start_pos)

    def generate_unique_color(self):
        # Define colors to avoid
        avoid_colors = {(0, 0, 0), (25, 25, 25), (125, 125, 125),(255,255,255)}  # Background, grid line, snack colors

        # Generate a random color and ensure it's not in the avoid list
        while True:
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            if color not in avoid_colors:
                return color

    def remove_player(self, user_id):
        if user_id in self.players:
            del self.players[user_id]

    def move_player(self, user_id, direction):
        if user_id in self.players:
            snake = self.players[user_id]
            dir_mapping = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}
            if direction in dir_mapping:
                snake.turns[snake.head.pos[:]] = dir_mapping[direction]
            snake.move()

            self.check_snack_consumption(user_id)
            if self.check_collision(user_id) or self.is_out_of_bounds(user_id):
                self.reset_player(user_id)

    def reset_player(self, user_id):
        start_pos = (random.randint(1, self.rows - 1), random.randint(1, self.rows - 1))
        self.players[user_id].reset(start_pos)

    def check_collision(self, user_id):
        player = self.players[user_id]
        head_pos = player.get_head_position()
        for segment in player.get_positions()[1:]:
            if head_pos == segment:
                return True
        return False
    
    def is_out_of_bounds(self, user_id):
        player = self.players[user_id]
        x, y = player.get_head_position()
        return not (0 <= x < self.rows and 0 <= y < self.rows)

    def check_snack_consumption(self, user_id):
        player = self.players[user_id]
        head_pos = player.get_head_position()
        for snack in self.snacks:
            if head_pos == snack.pos:
                self.snacks.remove(snack)
                self.snacks.append(self.random_snack())
                player.add_cube()
                break

    def get_state(self):
        game_state = {
            "snakes": {user_id: {"positions": player.get_positions(), "color": player.color}
                       for user_id, player in self.players.items()},
            "snacks": [snack.pos for snack in self.snacks]
        }
        return json.dumps(game_state)

    def random_snack(self):
        return Cube((random.randint(1, self.rows - 1), random.randint(1, self.rows - 1)), color=(0, 255, 0))
