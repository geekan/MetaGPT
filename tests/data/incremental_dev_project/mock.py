#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/17
@Author  : mannaandpoem
@File    : mock.py
"""
NEW_REQUIREMENT_SAMPLE = """
Adding graphical interface functionality to enhance the user experience in the number-guessing game. The existing number-guessing game currently relies on command-line input for numbers. The goal is to introduce a graphical interface to improve the game's usability and visual appeal
"""

PRD_SAMPLE = """
## Language

en_us

## Programming Language

Python

## Original Requirements

Make a simple number guessing game

## Product Goals

- Ensure a user-friendly interface for the game
- Provide a challenging yet enjoyable game experience
- Design the game to be easily extendable for future features

## User Stories

- As a player, I want to guess numbers and receive feedback on whether my guess is too high or too low
- As a player, I want to be able to set the difficulty level by choosing the range of possible numbers
- As a player, I want to see my previous guesses to strategize my next guess
- As a player, I want to know how many attempts it took me to guess the number once I get it right

## Competitive Analysis

- Guess The Number Game A: Basic text interface, no difficulty levels
- Number Master B: Has difficulty levels, but cluttered interface
- Quick Guess C: Sleek design, but lacks performance tracking
- NumGuess D: Good performance tracking, but not mobile-friendly
- GuessIt E: Mobile-friendly, but too many ads
- Perfect Guess F: Offers hints, but the hints are not very helpful
- SmartGuesser G: Has a learning mode, but lacks a competitive edge

## Competitive Quadrant Chart

quadrantChart
    title "User Engagement and Game Complexity"
    x-axis "Low Complexity" --> "High Complexity"
    y-axis "Low Engagement" --> "High Engagement"
    quadrant-1 "Too Simple"
    quadrant-2 "Niche Appeal"
    quadrant-3 "Complex & Unengaging"
    quadrant-4 "Sweet Spot"
    "Guess The Number Game A": [0.2, 0.4]
    "Number Master B": [0.5, 0.3]
    "Quick Guess C": [0.6, 0.7]
    "NumGuess D": [0.4, 0.6]
    "GuessIt E": [0.7, 0.5]
    "Perfect Guess F": [0.6, 0.4]
    "SmartGuesser G": [0.8, 0.6]
    "Our Target Product": [0.5, 0.8]

## Requirement Analysis

The game should be simple yet engaging, allowing players of different skill levels to enjoy it. It should provide immediate feedback and track the player's performance. The game should also be designed with a clean and intuitive interface, and it should be easy to add new features in the future.

## Requirement Pool

- ['P0', 'Implement the core game logic to randomly select a number and allow the user to guess it']
- ['P0', 'Design a user interface that displays the game status and results clearly']
- ['P1', 'Add difficulty levels by varying the range of possible numbers']
- ['P1', 'Keep track of and display the number of attempts for each game session']
- ['P2', "Store and show the history of the player's guesses during a game session"]

## UI Design draft

The UI will feature a clean and minimalist design with a number input field, submit button, and messages area to provide feedback. There will be options to select the difficulty level and a display showing the number of attempts and history of past guesses.

## Anything UNCLEAR"""

DESIGN_SAMPLE = """
## Implementation approach

We will create a Python-based number guessing game with a simple command-line interface. For the user interface, we will use the built-in 'input' and 'print' functions for interaction. The random library will be used for generating random numbers. We will structure the code to be modular and easily extendable, separating the game logic from the user interface.

## File list

- main.py
- game.py
- ui.py

## Data structures and interfaces


classDiagram
    class Game {
        -int secret_number
        -int min_range
        -int max_range
        -list attempts
        +__init__(difficulty: str)
        +start_game()
        +check_guess(guess: int) str
        +get_attempts() int
        +get_history() list
    }
    class UI {
        +start()
        +display_message(message: str)
        +get_user_input(prompt: str) str
        +show_attempts(attempts: int)
        +show_history(history: list)
        +select_difficulty() str
    }
    class Main {
        +main()
    }
    Main --> UI
    UI --> Game


## Program call flow


sequenceDiagram
    participant M as Main
    participant UI as UI
    participant G as Game
    M->>UI: start()
    UI->>UI: select_difficulty()
    UI-->>G: __init__(difficulty)
    G->>G: start_game()
    loop Game Loop
        UI->>UI: get_user_input("Enter your guess:")
        UI-->>G: check_guess(guess)
        G->>UI: display_message(feedback)
        G->>UI: show_attempts(attempts)
        G->>UI: show_history(history)
    end
    G->>UI: display_message("Correct! Game over.")
    UI->>M: main()  # Game session ends


## Anything UNCLEAR

The requirement analysis suggests the need for a clean and intuitive interface. Since we are using a command-line interface, we need to ensure that the text-based UI is as user-friendly as possible. Further clarification on whether a graphical user interface (GUI) is expected in the future would be helpful for planning the extendability of the game."""

TASK_SAMPLE = """
## Required Python packages

- random==2.2.1

## Required Other language third-party packages

- No third-party dependencies required

## Logic Analysis

- ['game.py', 'Contains Game class with methods __init__, start_game, check_guess, get_attempts, get_history and uses random library for generating secret_number']
- ['ui.py', 'Contains UI class with methods start, display_message, get_user_input, show_attempts, show_history, select_difficulty and interacts with Game class']
- ['main.py', 'Contains Main class with method main that initializes UI class and starts the game loop']

## Task list

- game.py
- ui.py
- main.py

## Full API spec



## Shared Knowledge

`game.py` contains the core game logic and is used by `ui.py` to interact with the user. `main.py` serves as the entry point to start the game.

## Anything UNCLEAR

The requirement analysis suggests the need for a clean and intuitive interface. Since we are using a command-line interface, we need to ensure that the text-based UI is as user-friendly as possible. Further clarification on whether a graphical user interface (GUI) is expected in the future would be helpful for planning the extendability of the game."""

OLD_CODE_SAMPLE = """
--- game.py
```## game.py

import random

class Game:
    def __init__(self, difficulty: str = 'medium'):
        self.min_range, self.max_range = self._set_difficulty(difficulty)
        self.secret_number = random.randint(self.min_range, self.max_range)
        self.attempts = []

    def _set_difficulty(self, difficulty: str):
        difficulties = {
            'easy': (1, 10),
            'medium': (1, 100),
            'hard': (1, 1000)
        }
        return difficulties.get(difficulty, (1, 100))

    def start_game(self):
        self.secret_number = random.randint(self.min_range, self.max_range)
        self.attempts = []

    def check_guess(self, guess: int) -> str:
        self.attempts.append(guess)
        if guess < self.secret_number:
            return "It's higher."
        elif guess > self.secret_number:
            return "It's lower."
        else:
            return "Correct! Game over."

    def get_attempts(self) -> int:
        return len(self.attempts)

    def get_history(self) -> list:
        return self.attempts```

--- ui.py
```## ui.py

from game import Game

class UI:
    def start(self):
        difficulty = self.select_difficulty()
        game = Game(difficulty)
        game.start_game()
        self.display_welcome_message(game)

        feedback = ""
        while feedback != "Correct! Game over.":
            guess = self.get_user_input("Enter your guess: ")
            if self.is_valid_guess(guess):
                feedback = game.check_guess(int(guess))
                self.display_message(feedback)
                self.show_attempts(game.get_attempts())
                self.show_history(game.get_history())
            else:
                self.display_message("Please enter a valid number.")

    def display_welcome_message(self, game):
        print("Welcome to the Number Guessing Game!")
        print(f"Guess the number between {game.min_range} and {game.max_range}.")

    def is_valid_guess(self, guess):
        return guess.isdigit()

    def display_message(self, message: str):
        print(message)

    def get_user_input(self, prompt: str) -> str:
        return input(prompt)

    def show_attempts(self, attempts: int):
        print(f"Number of attempts: {attempts}")

    def show_history(self, history: list):
        print("Guess history:")
        for guess in history:
            print(guess)

    def select_difficulty(self) -> str:
        while True:
            difficulty = input("Select difficulty (easy, medium, hard): ").lower()
            if difficulty in ['easy', 'medium', 'hard']:
                return difficulty
            else:
                self.display_message("Invalid difficulty. Please choose 'easy', 'medium', or 'hard'.")```

--- main.py
```## main.py

from ui import UI

class Main:
    def main(self):
        user_interface = UI()
        user_interface.start()

if __name__ == "__main__":
    main_instance = Main()
    main_instance.main()```
"""

REFINED_PRD_JSON = {
    "Language": "en_us",
    "Programming Language": "Python",
    "Refined Requirements": "Adding graphical interface functionality to enhance the user experience in the number-guessing game.",
    "Project Name": "number_guessing_game",
    "Refined Product Goals": [
        "Ensure a user-friendly interface for the game with the new graphical interface",
        "Provide a challenging yet enjoyable game experience with visual enhancements",
        "Design the game to be easily extendable for future features, including graphical elements",
    ],
    "Refined User Stories": [
        "As a player, I want to interact with a graphical interface to guess numbers and receive visual feedback on my guesses",
        "As a player, I want to easily select the difficulty level through the graphical interface",
        "As a player, I want to visually track my previous guesses and the number of attempts in the graphical interface",
        "As a player, I want to be congratulated with a visually appealing message when I guess the number correctly",
    ],
    "Competitive Analysis": [
        "Guess The Number Game A: Basic text interface, no difficulty levels",
        "Number Master B: Has difficulty levels, but cluttered interface",
        "Quick Guess C: Sleek design, but lacks performance tracking",
        "NumGuess D: Good performance tracking, but not mobile-friendly",
        "GuessIt E: Mobile-friendly, but too many ads",
        "Perfect Guess F: Offers hints, but the hints are not very helpful",
        "SmartGuesser G: Has a learning mode, but lacks a competitive edge",
        "Graphical Guess H: Graphical interface, but poor user experience due to complex design",
    ],
    "Competitive Quadrant Chart": 'quadrantChart\n    title "User Engagement and Game Complexity with Graphical Interface"\n    x-axis "Low Complexity" --> "High Complexity"\n    y-axis "Low Engagement" --> "High Engagement"\n    quadrant-1 "Too Simple"\n    quadrant-2 "Niche Appeal"\n    quadrant-3 "Complex & Unengaging"\n    quadrant-4 "Sweet Spot"\n    "Guess The Number Game A": [0.2, 0.4]\n    "Number Master B": [0.5, 0.3]\n    "Quick Guess C": [0.6, 0.7]\n    "NumGuess D": [0.4, 0.6]\n    "GuessIt E": [0.7, 0.5]\n    "Perfect Guess F": [0.6, 0.4]\n    "SmartGuesser G": [0.8, 0.6]\n    "Graphical Guess H": [0.7, 0.3]\n    "Our Target Product": [0.5, 0.9]',
    "Refined Requirement Analysis": [
        "The game should maintain its simplicity while integrating a graphical interface for enhanced engagement.",
        "Immediate visual feedback is crucial for user satisfaction in the graphical interface.",
        "The interface must be intuitive, allowing for easy navigation and selection of game options.",
        "The graphical design should be clean and not detract from the game's core guessing mechanic.",
    ],
    "Refined Requirement Pool": [
        ["P0", "Implement a graphical user interface (GUI) to replace the command-line interaction"],
        [
            "P0",
            "Design a user interface that displays the game status, results, and feedback clearly with graphical elements",
        ],
        ["P1", "Incorporate interactive elements for selecting difficulty levels"],
        ["P1", "Visualize the history of the player's guesses and the number of attempts within the game session"],
        ["P2", "Create animations for correct or incorrect guesses to enhance user feedback"],
        ["P2", "Ensure the GUI is responsive and compatible with various screen sizes"],
        ["P2", "Store and show the history of the player's guesses during a game session"],
    ],
    "UI Design draft": "The UI will feature a modern and minimalist design with a graphical number input field, a submit button with animations, and a dedicated area for visual feedback. It will include interactive elements to select the difficulty level and a visual display for the number of attempts and history of past guesses.",
    "Anything UNCLEAR": "",
}

REFINED_DESIGN_JSON = {
    "Refined Implementation Approach": "To accommodate the new graphical user interface (GUI) requirements, we will leverage the Tkinter library, which is included with Python and supports the creation of a user-friendly GUI. The game logic will remain in Python, with Tkinter handling the rendering of the interface. We will ensure that the GUI is responsive and provides immediate visual feedback. The main game loop will be event-driven, responding to user inputs such as button clicks and difficulty selection.",
    "Refined File list": ["main.py", "game.py", "ui.py", "gui.py"],
    "Refined Data structures and interfaces": "\nclassDiagram\n    class Game {\n        -int secret_number\n        -int min_range\n        -int max_range\n        -list attempts\n        +__init__(difficulty: str)\n        +start_game()\n        +check_guess(guess: int) str\n        +get_attempts() int\n        +get_history() list\n    }\n    class UI {\n        +start()\n        +display_message(message: str)\n        +get_user_input(prompt: str) str\n        +show_attempts(attempts: int)\n        +show_history(history: list)\n        +select_difficulty() str\n    }\n    class GUI {\n        +__init__()\n        +setup_window()\n        +bind_events()\n        +update_feedback(message: str)\n        +update_attempts(attempts: int)\n        +update_history(history: list)\n        +show_difficulty_selector()\n        +animate_guess_result(correct: bool)\n    }\n    class Main {\n        +main()\n    }\n    Main --> UI\n    UI --> Game\n    UI --> GUI\n    GUI --> Game\n",
    "Refined Program call flow": '\nsequenceDiagram\n    participant M as Main\n    participant UI as UI\n    participant G as Game\n    participant GU as GUI\n    M->>UI: start()\n    UI->>GU: setup_window()\n    GU->>GU: bind_events()\n    GU->>UI: select_difficulty()\n    UI-->>G: __init__(difficulty)\n    G->>G: start_game()\n    loop Game Loop\n        GU->>GU: show_difficulty_selector()\n        GU->>UI: get_user_input("Enter your guess:")\n        UI-->>G: check_guess(guess)\n        G->>GU: update_feedback(feedback)\n        G->>GU: update_attempts(attempts)\n        G->>GU: update_history(history)\n        GU->>GU: animate_guess_result(correct)\n    end\n    G->>GU: update_feedback("Correct! Game over.")\n    GU->>M: main()  # Game session ends\n',
    "Anything UNCLEAR": "",
}

REFINED_TASK_JSON = {
    "Required Python packages": ["random==2.2.1", "Tkinter==8.6"],
    "Required Other language third-party packages": ["No third-party dependencies required"],
    "Refined Logic Analysis": [
        [
            "game.py",
            "Contains Game class with methods __init__, start_game, check_guess, get_attempts, get_history and uses random library for generating secret_number",
        ],
        [
            "ui.py",
            "Contains UI class with methods start, display_message, get_user_input, show_attempts, show_history, select_difficulty and interacts with Game class",
        ],
        [
            "gui.py",
            "Contains GUI class with methods __init__, setup_window, bind_events, update_feedback, update_attempts, update_history, show_difficulty_selector, animate_guess_result and interacts with Game class for GUI rendering",
        ],
        [
            "main.py",
            "Contains Main class with method main that initializes UI class and starts the event-driven game loop",
        ],
    ],
    "Refined Task list": ["game.py", "ui.py", "gui.py", "main.py"],
    "Full API spec": "",
    "Refined Shared Knowledge": "`game.py` contains the core game logic and is used by `ui.py` to interact with the user. `main.py` serves as the entry point to start the game. `gui.py` is introduced to handle the graphical user interface using Tkinter, which will interact with both `game.py` and `ui.py` for a responsive and user-friendly experience.",
    "Anything UNCLEAR": "",
}

CODE_PLAN_AND_CHANGE_SAMPLE = {
    "Development Plan": [
        "Develop the GUI using Tkinter to replace the command-line interface. Start by setting up the main window and event handling. Then, add widgets for displaying the game status, results, and feedback. Implement interactive elements for difficulty selection and visualize the guess history. Finally, create animations for guess feedback and ensure responsiveness across different screen sizes.",
        "Modify the main.py to initialize the GUI and start the event-driven game loop. Ensure that the GUI is the primary interface for user interaction.",
    ],
    "Incremental Change": [
        """```diff\nclass GUI:\n-    pass\n+    def __init__(self):\n+        self.setup_window()\n+\n+    def setup_window(self):\n+        # Initialize the main window using Tkinter\n+        pass\n+\n+    def bind_events(self):\n+        # Bind button clicks and other events\n+        pass\n+\n+    def update_feedback(self, message: str):\n+        # Update the feedback label with the given message\n+        pass\n+\n+    def update_attempts(self, attempts: int):\n+        # Update the attempts label with the number of attempts\n+        pass\n+\n+    def update_history(self, history: list):\n+        # Update the history view with the list of past guesses\n+        pass\n+\n+    def show_difficulty_selector(self):\n+        # Show buttons or a dropdown for difficulty selection\n+        pass\n+\n+    def animate_guess_result(self, correct: bool):\n+        # Trigger an animation for correct or incorrect guesses\n+        pass\n```""",
        """```diff\nclass Main:\n     def main(self):\n-        user_interface = UI()\n-        user_interface.start()\n+        graphical_user_interface = GUI()\n+        graphical_user_interface.setup_window()\n+        graphical_user_interface.bind_events()\n+        # Start the Tkinter main loop\n+        pass\n\n if __name__ == "__main__":\n     main_instance = Main()\n     main_instance.main()\n```\n\n3. Plan for ui.py: Refactor ui.py to work with the new GUI class. Remove command-line interactions and delegate display and input tasks to the GUI.\n```python\nclass UI:\n-    def display_message(self, message: str):\n-        print(message)\n+\n+    def display_message(self, message: str):\n+        # This method will now pass the message to the GUI to display\n+        pass\n\n-    def get_user_input(self, prompt: str) -> str:\n-        return input(prompt)\n+\n+    def get_user_input(self, prompt: str) -> str:\n+        # This method will now trigger the GUI to get user input\n+        pass\n\n-    def show_attempts(self, attempts: int):\n-        print(f"Number of attempts: {attempts}")\n+\n+    def show_attempts(self, attempts: int):\n+        # This method will now update the GUI with the number of attempts\n+        pass\n\n-    def show_history(self, history: list):\n-        print("Guess history:")\n-        for guess in history:\n-            print(guess)\n+\n+    def show_history(self, history: list):\n+        # This method will now update the GUI with the guess history\n+        pass\n```\n\n4. Plan for game.py: Ensure game.py remains mostly unchanged as it contains the core game logic. However, make minor adjustments if necessary to integrate with the new GUI.\n```python\nclass Game:\n     # No changes required for now\n```\n""",
    ],
}

REFINED_CODE_INPUT_SAMPLE = """
-----Now, game.py to be rewritten
```## game.py

import random

class Game:
    def __init__(self, difficulty: str = 'medium'):
        self.min_range, self.max_range = self._set_difficulty(difficulty)
        self.secret_number = random.randint(self.min_range, self.max_range)
        self.attempts = []

    def _set_difficulty(self, difficulty: str):
        difficulties = {
            'easy': (1, 10),
            'medium': (1, 100),
            'hard': (1, 1000)
        }
        return difficulties.get(difficulty, (1, 100))

    def start_game(self):
        self.secret_number = random.randint(self.min_range, self.max_range)
        self.attempts = []

    def check_guess(self, guess: int) -> str:
        self.attempts.append(guess)
        if guess < self.secret_number:
            return "It's higher."
        elif guess > self.secret_number:
            return "It's lower."
        else:
            return "Correct! Game over."

    def get_attempts(self) -> int:
        return len(self.attempts)

    def get_history(self) -> list:
        return self.attempts```
"""

REFINED_CODE_SAMPLE = """
## game.py

import random

class Game:
    def __init__(self, difficulty: str = 'medium'):
        # Set the difficulty level with default value 'medium'
        self.min_range, self.max_range = self._set_difficulty(difficulty)
        # Initialize the secret number based on the difficulty
        self.secret_number = random.randint(self.min_range, self.max_range)
        # Initialize the list to keep track of attempts
        self.attempts = []

    def _set_difficulty(self, difficulty: str):
        # Define the range of numbers for each difficulty level
        difficulties = {
            'easy': (1, 10),
            'medium': (1, 100),
            'hard': (1, 1000)
        }
        # Return the corresponding range for the selected difficulty, default to 'medium' if not found
        return difficulties.get(difficulty, (1, 100))

    def start_game(self):
        # Reset the secret number and attempts list for a new game
        self.secret_number = random.randint(self.min_range, self.max_range)
        self.attempts.clear()

    def check_guess(self, guess: int) -> str:
        # Add the guess to the attempts list
        self.attempts.append(guess)
        # Provide feedback based on the guess
        if guess < self.secret_number:
            return "It's higher."
        elif guess > self.secret_number:
            return "It's lower."
        else:
            return "Correct! Game over."

    def get_attempts(self) -> int:
        # Return the number of attempts made
        return len(self.attempts)

    def get_history(self) -> list:
        # Return the list of attempts made
        return self.attempts
"""
