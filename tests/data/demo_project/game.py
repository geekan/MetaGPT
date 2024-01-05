## game.py

import random
from typing import List, Tuple


class Game:
    def __init__(self):
        self.grid: List[List[int]] = [[0 for _ in range(4)] for _ in range(4)]
        self.score: int = 0
        self.game_over: bool = False

    def reset_game(self):
        self.grid = [[0 for _ in range(4)] for _ in range(4)]
        self.score = 0
        self.game_over = False
        self.add_new_tile()
        self.add_new_tile()

    def move(self, direction: str):
        if direction == "up":
            self._move_up()
        elif direction == "down":
            self._move_down()
        elif direction == "left":
            self._move_left()
        elif direction == "right":
            self._move_right()

    def is_game_over(self) -> bool:
        for i in range(4):
            for j in range(4):
                if self.grid[i][j] == 0:
                    return False
                if j < 3 and self.grid[i][j] == self.grid[i][j + 1]:
                    return False
                if i < 3 and self.grid[i][j] == self.grid[i + 1][j]:
                    return False
        return True

    def get_empty_cells(self) -> List[Tuple[int, int]]:
        empty_cells = []
        for i in range(4):
            for j in range(4):
                if self.grid[i][j] == 0:
                    empty_cells.append((i, j))
        return empty_cells

    def add_new_tile(self):
        empty_cells = self.get_empty_cells()
        if empty_cells:
            x, y = random.choice(empty_cells)
            self.grid[x][y] = 2 if random.random() < 0.9 else 4

    def get_score(self) -> int:
        return self.score

    def _move_up(self):
        for j in range(4):
            for i in range(1, 4):
                if self.grid[i][j] != 0:
                    for k in range(i, 0, -1):
                        if self.grid[k - 1][j] == 0:
                            self.grid[k - 1][j] = self.grid[k][j]
                            self.grid[k][j] = 0

    def _move_down(self):
        for j in range(4):
            for i in range(2, -1, -1):
                if self.grid[i][j] != 0:
                    for k in range(i, 3):
                        if self.grid[k + 1][j] == 0:
                            self.grid[k + 1][j] = self.grid[k][j]
                            self.grid[k][j] = 0

    def _move_left(self):
        for i in range(4):
            for j in range(1, 4):
                if self.grid[i][j] != 0:
                    for k in range(j, 0, -1):
                        if self.grid[i][k - 1] == 0:
                            self.grid[i][k - 1] = self.grid[i][k]
                            self.grid[i][k] = 0

    def _move_right(self):
        for i in range(4):
            for j in range(2, -1, -1):
                if self.grid[i][j] != 0:
                    for k in range(j, 3):
                        if self.grid[i][k + 1] == 0:
                            self.grid[i][k + 1] = self.grid[i][k]
                            self.grid[i][k] = 0
