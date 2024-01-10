## Implementation approach

We will use the Pygame library to create the game interface and handle user input. The game logic will be implemented using Python classes and data structures.

## File list

- main.py
- game.py

## Data structures and interfaces

classDiagram
    class Game {
        -grid: List[List[int]]
        -score: int
        -game_over: bool
        +__init__()
        +reset_game()
        +move(direction: str)
        +is_game_over() bool
        +get_empty_cells() List[Tuple[int, int]]
        +add_new_tile()
        +get_score() int
    }
    class UI {
        -game: Game
        +__init__(game: Game)
        +draw_grid()
        +draw_score()
        +draw_game_over()
        +handle_input()
    }
    Game --> UI

## Program call flow

sequenceDiagram
    participant M as Main
    participant G as Game
    participant U as UI
    M->>G: reset_game()
    M->>U: draw_grid()
    M->>U: draw_score()
    M->>U: handle_input()
    U->>G: move(direction)
    G->>G: add_new_tile()
    G->>U: draw_grid()
    G->>U: draw_score()
    G->>U: draw_game_over()
    G->>G: is_game_over()
    G->>G: get_empty_cells()
    G->>G: get_score()

## Anything UNCLEAR

...

