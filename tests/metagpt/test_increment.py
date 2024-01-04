#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_increment.py
"""
import pytest
from typer.testing import CliRunner

from metagpt.logs import logger
from metagpt.startup import app

runner = CliRunner()


def test_refined_simple_calculator():
    args = [
        "Add subtraction, multiplication and division operations to the calculator. The current calculator can only perform basic addition operations, and it is necessary to introduce subtraction, multiplication, division operation into the calculator",
        "--inc",
        "--project-path",
        "data/simple_add_calculator",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_number_guessing_game():
    args = [
        "Adding graphical interface functionality to enhance the user experience in the number-guessing game. The existing number-guessing game currently relies on command-line input for numbers. The goal is to introduce a graphical interface to improve the game's usability and visual appeal",
        "--inc",
        "--project-path",
        "data/number_guessing_game",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_dice_simulator_1():
    args = [
        "Add functionality to view the history of scores. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores",
        "--inc",
        "--project-path",
        "data/dice_simulator_new",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_dice_simulator_2():
    args = [
        "Add functionality to view the history of scores and perform statistical analysis on them. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores and display the statistical analysis results of the current score",
        "--inc",
        "--project-path",
        "data/dice_simulator_new",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_dice_simulator_3():
    args = [
        "Add functionality to set the number of sides on a die; Add functionality to view the history of scores;  Add functionality to perform statistical analysis on all scores. The original dice rolling game could roll the dice multiple times and only display the current game result. But the new requirement add function that players to customize the number of sides of the dice and to view the history of scores and display the statistical analysis",
        "--inc",
        "--project-path",
        "data/dice_simulator_new",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_pygame_2048_1():
    args = [
        "Changed score target for 2048 game from 2048 to 4096. Please change the game's score target from 2048 to 4096, and change the interface size from 4*4 to 8*8",
        "--inc",
        "--project-path",
        "data/pygame_2048",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_pygame_2048_2():
    args = [
        "Display the history score of the player in the 2048 game. Add a record board that can display players' historical score records so that players can trace their scores",
        "--inc",
        "--project-path",
        "data/pygame_2048",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_pygame_2048_3():
    args = [
        "Add limited time mode. The original game only had a default classic mode. The improved game should be able to support limited-time mode, allowing users to choose classic mode or limited-time mode from the available options before starting the game.",
        "--inc",
        "--project-path",
        "data/pygame_2048",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_word_cloud_1():
    args = [
        "Add a feature to remove deprecated words from the word cloud. The current word cloud generator does not support removing deprecated words. Now, The word cloud generator should support removing deprecated words. Customize deactivated words to exclude them from word cloud. Let users see all the words in the text file, and allow users to select the words they want to remove.",
        "--inc",
        "--project-path",
        "data/word_cloud",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


def test_refined_word_cloud_2():
    args = [
        "Add a feature to customize the resolution of the word cloud.The new version allows users to customize the size and resolution of the generated word cloud after uploading a text file, and then generate the word cloud.",
        "--inc",
        "--project-path",
        "data/word_cloud",
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
