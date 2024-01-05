#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_incremental_dev.py
"""
import os

import pytest
from typer.testing import CliRunner

from metagpt.const import DATA_PATH
from metagpt.logs import logger
from metagpt.startup import app

runner = CliRunner()


def test_refined_simple_calculator():
    project_path = f"{DATA_PATH}/simple_add_calculator"
    check_or_create_base_tag(project_path)

    args = [
        "Add subtraction, multiplication and division operations to the calculator. The current calculator can only perform basic addition operations, and it is necessary to introduce subtraction, multiplication, division operation into the calculator",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine")
    logger.info(result)
    logger.info(result.output)


def test_refined_number_guessing_game():
    project_path = f"{DATA_PATH}/number_guessing_game"
    check_or_create_base_tag(project_path)

    args = [
        "Adding graphical interface functionality to enhance the user experience in the number-guessing game. The existing number-guessing game currently relies on command-line input for numbers. The goal is to introduce a graphical interface to improve the game's usability and visual appeal",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine")
    logger.info(result)
    logger.info(result.output)


def test_refined_dice_simulator_1():
    project_path = f"{DATA_PATH}/dice_simulator_new"
    check_or_create_base_tag(project_path)

    args = [
        "Add functionality to view the history of scores. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores",
        "--inc",
        "--project-path",
        project_path,
        "--no-code-review",
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine_1")
    logger.info(result)
    logger.info(result.output)


def test_refined_dice_simulator_2():
    project_path = f"{DATA_PATH}/dice_simulator_new"
    check_or_create_base_tag(project_path)

    args = [
        "Add functionality to view the history of scores and perform statistical analysis on them. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores and display the statistical analysis results of the current score",
        "--inc",
        "--project-path",
        project_path,
        "--no-code-review",
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine_2")
    logger.info(result)
    logger.info(result.output)


def test_refined_dice_simulator_3():
    project_path = f"{DATA_PATH}/dice_simulator_new"
    check_or_create_base_tag(project_path)

    args = [
        "Add functionality to set the number of sides on a die; Add functionality to view the history of scores;  Add functionality to perform statistical analysis on all scores. The original dice rolling game could roll the dice multiple times and only display the current game result. But the new requirement add function that players to customize the number of sides of the dice and to view the history of scores and display the statistical analysis",
        "--inc",
        "--project-path",
        project_path,
        "--no-code-review",
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine_3")
    logger.info(result)
    logger.info(result.output)


def test_refined_pygame_2048_1():
    project_path = f"{DATA_PATH}/pygame_2048"
    check_or_create_base_tag(project_path)

    args = [
        "Changed score target for 2048 game from 2048 to 4096. Please change the game's score target from 2048 to 4096, and change the interface size from 4*4 to 8*8",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine_1")
    logger.info(result)
    logger.info(result.output)


def test_refined_pygame_2048_2():
    project_path = f"{DATA_PATH}/pygame_2048"
    check_or_create_base_tag(project_path)

    args = [
        "Display the history score of the player in the 2048 game. Add a record board that can display players' historical score records so that players can trace their scores",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine_2")
    logger.info(result)
    logger.info(result.output)


def test_refined_pygame_2048_3():
    project_path = f"{DATA_PATH}/pygame_2048"
    check_or_create_base_tag(project_path)

    args = [
        "Add limited time mode. The original game only had a default classic mode. The improved game should be able to support limited-time mode, allowing users to choose classic mode or limited-time mode from the available options before starting the game.",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine_3")
    logger.info(result)
    logger.info(result.output)


def test_refined_word_cloud_1():
    project_path = f"{DATA_PATH}/word_cloud"
    check_or_create_base_tag(project_path)

    args = [
        "Add a feature to remove deprecated words from the word cloud. The current word cloud generator does not support removing deprecated words. Now, The word cloud generator should support removing deprecated words. Customize deactivated words to exclude them from word cloud. Let users see all the words in the text file, and allow users to select the words they want to remove.",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine_1")
    logger.info(result)
    logger.info(result.output)


def test_refined_word_cloud_2():
    project_path = f"{DATA_PATH}/word_cloud"
    check_or_create_base_tag(project_path)

    args = [
        "Add a feature to customize the resolution of the word cloud.The new version allows users to customize the size and resolution of the generated word cloud after uploading a text file, and then generate the word cloud.",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    os.system("git tag refine_2")
    logger.info(result)
    logger.info(result.output)


def check_or_create_base_tag(project_path):
    # Change the current working directory to the specified project path
    os.chdir(project_path)

    # Initialize a Git repository
    os.system("git init")

    # Check if the 'base' tag exists
    check_base_tag_cmd = "git show-ref --verify --quiet refs/tags/base"
    has_base_tag = os.system(check_base_tag_cmd) == 0

    if has_base_tag:
        logger.info("Base tag exists")
        # Switch to the 'base' branch if it exists
        switch_to_base_branch_cmd = "git checkout base"
        try:
            os.system(switch_to_base_branch_cmd)
            logger.info("Switched to base branch")
        except Exception as e:
            logger.info("Failed to switch to base branch")
            raise e

    else:
        logger.info("Base tag doesn't exist.")
        # Add and commit the current code if 'base' tag doesn't exist
        add_cmd = "git add ."
        commit_cmd = 'git commit -m "Initial commit"'
        try:
            os.system(add_cmd)
            os.system(commit_cmd)
            logger.info("Added and committed all files with the message 'Initial commit'.")
        except Exception as e:
            logger.info("Failed to add and commit all files.")
            raise e

        # Add 'base' tag
        add_base_tag_cmd = "git tag base"

        # Check if the 'git tag' command was successful
        try:
            os.system(add_base_tag_cmd)
            logger.info("Added 'base' tag.")
        except Exception as e:
            logger.info("Failed to add 'base' tag.")
            raise e


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
