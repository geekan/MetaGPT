#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : test_debug_error.py
"""
import pytest

from metagpt.actions.debug_error import DebugError

EXAMPLE_MSG_CONTENT = '''
---
## Development Code File Name
player.py
## Development Code
```python
from typing import List
from deck import Deck
from card import Card

class Player:
    """
    A class representing a player in the Black Jack game.
    """

    def __init__(self, name: str):
        """
        Initialize a Player object.
        
        Args:
            name (str): The name of the player.
        """
        self.name = name
        self.hand: List[Card] = []
        self.score = 0

    def draw(self, deck: Deck):
        """
        Draw a card from the deck and add it to the player's hand.
        
        Args:
            deck (Deck): The deck of cards.
        """
        card = deck.draw_card()
        self.hand.append(card)
        self.calculate_score()

    def calculate_score(self) -> int:
        """
        Calculate the score of the player's hand.
        
        Returns:
            int: The score of the player's hand.
        """
        self.score = sum(card.value for card in self.hand)
        # Handle the case where Ace is counted as 11 and causes the score to exceed 21
        if self.score > 21 and any(card.rank == 'A' for card in self.hand):
            self.score -= 10
        return self.score

```
## Test File Name
test_player.py
## Test Code
```python
import unittest
from blackjack_game.player import Player
from blackjack_game.deck import Deck
from blackjack_game.card import Card

class TestPlayer(unittest.TestCase):
    ## Test the Player's initialization
    def test_player_initialization(self):
        player = Player("Test Player")
        self.assertEqual(player.name, "Test Player")
        self.assertEqual(player.hand, [])
        self.assertEqual(player.score, 0)

    ## Test the Player's draw method
    def test_player_draw(self):
        deck = Deck()
        player = Player("Test Player")
        player.draw(deck)
        self.assertEqual(len(player.hand), 1)
        self.assertEqual(player.score, player.hand[0].value)

    ## Test the Player's calculate_score method
    def test_player_calculate_score(self):
        deck = Deck()
        player = Player("Test Player")
        player.draw(deck)
        player.draw(deck)
        self.assertEqual(player.score, sum(card.value for card in player.hand))

    ## Test the Player's calculate_score method with Ace card
    def test_player_calculate_score_with_ace(self):
        deck = Deck()
        player = Player("Test Player")
        player.hand.append(Card('A', 'Hearts', 11))
        player.hand.append(Card('K', 'Hearts', 10))
        player.calculate_score()
        self.assertEqual(player.score, 21)

    ## Test the Player's calculate_score method with multiple Aces
    def test_player_calculate_score_with_multiple_aces(self):
        deck = Deck()
        player = Player("Test Player")
        player.hand.append(Card('A', 'Hearts', 11))
        player.hand.append(Card('A', 'Diamonds', 11))
        player.calculate_score()
        self.assertEqual(player.score, 12)

if __name__ == '__main__':
    unittest.main()

```
## Running Command
python tests/test_player.py
## Running Output
standard output: ;
standard errors: ..F..
======================================================================
FAIL: test_player_calculate_score_with_multiple_aces (__main__.TestPlayer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_player.py", line 46, in test_player_calculate_score_with_multiple_aces
    self.assertEqual(player.score, 12)
AssertionError: 22 != 12

----------------------------------------------------------------------
Ran 5 tests in 0.007s

FAILED (failures=1)
;
## instruction:
The error is in the development code, specifically in the calculate_score method of the Player class. The method is not correctly handling the case where there are multiple Aces in the player's hand. The current implementation only subtracts 10 from the score once if the score is over 21 and there's an Ace in the hand. However, in the case of multiple Aces, it should subtract 10 for each Ace until the score is 21 or less.
## File To Rewrite:
player.py
## Status:
FAIL
## Send To:
Engineer
---
'''

@pytest.mark.asyncio
async def test_debug_error():

    debug_error = DebugError("debug_error")

    file_name, rewritten_code = await debug_error.run(context=EXAMPLE_MSG_CONTENT)

    assert "class Player" in rewritten_code # rewrite the same class
    assert "while self.score > 21" in rewritten_code # a key logic to rewrite to (original one is "if self.score > 12")
