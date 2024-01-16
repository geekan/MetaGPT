#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_incremental_dev.py
"""
import os
import subprocess

import pytest
from typer.testing import CliRunner

from metagpt.const import TEST_DATA_PATH
from metagpt.logs import logger
from metagpt.startup import app

runner = CliRunner()

IDEAS = [
    "Add subtraction, multiplication and division operations to the calculator. The current calculator can only perform basic addition operations, and it is necessary to introduce subtraction, multiplication, division operation into the calculator",
    "Add a feature to remove deprecated words from the word cloud. The current word cloud generator does not support removing deprecated words. Now, The word cloud generator should support removing deprecated words. Customize deactivated words to exclude them from word cloud. Let users see all the words in the text file, and allow users to select the words they want to remove.",
    "Add an AI opponent with fixed difficulty levels. Currently, the game only allows players to compete against themselves. Implement an AI algorithm that can playing with player. This will provide a more engaging and challenging experience for players.",
    "Add functionality to view the history of scores. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores",
    "Add functionality to view the history of scores and perform statistical analysis on them. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores and display the statistical analysis results of the current score",
    "Changed score target for 2048 game from 2048 to 4096. Please change the game's score target from 2048 to 4096, and change the interface size from 4*4 to 8*8",
    "Display the history score of the player in the 2048 game. Add a record board that can display players' historical score records so that players can trace their scores",
    "Add limited time mode. The original game only had a default classic mode. The improved game should be able to support limited-time mode, allowing users to choose classic mode or limited-time mode from the available options before starting the game.",
    "Incremental Idea Gradually increase the speed of the snake as the game progresses. In the current version of the game, the snake’s speed remains constant throughout the gameplay. Implement a feature where the snake’s speed gradually increases over time, making the game more challenging and intense as the player progresses.",
    "Introduce power-ups and obstacles to the game. The current version of the game only involves eating food and growing the snake. Add new elements such as power-ups that can enhance the snake’s speed or make it invincible for a short duration. At the same time, introduce obstacles like walls or enemies that the snake must avoid or overcome to continue growing.",
]

PROJECT_NAMES = [
    "calculator",
    "word_cloud",
    "Gomoku",
    "dice_simulator_new",
    "dice_simulator_new",
    "pygame_2048",
    "pygame_2048",
    "pygame_2048",
    "snake_game",
    "snake_game",
]


def test_refined_calculator():
    result = get_incremental_dev_result(IDEAS[0], PROJECT_NAMES[0])
    log_and_check_result(result)


def test_refined_word_cloud():
    result = get_incremental_dev_result(IDEAS[1], PROJECT_NAMES[1])
    log_and_check_result(result)


def test_refined_gomoku():
    result = get_incremental_dev_result(IDEAS[2], PROJECT_NAMES[2])
    log_and_check_result(result)


def test_refined_dice_simulator_new():
    for idea, project_name in zip(IDEAS[3:5], PROJECT_NAMES[3:5]):
        result = get_incremental_dev_result(idea, project_name)
        log_and_check_result(result)


def test_refined_pygame_2048():
    for idea, project_name in zip(IDEAS[5:8], PROJECT_NAMES[5:8]):
        result = get_incremental_dev_result(idea, project_name)
        log_and_check_result(result)


def test_refined_snake_game():
    for idea, project_name in zip(IDEAS[8:10], PROJECT_NAMES[8:10]):
        result = get_incremental_dev_result(idea, project_name)
        log_and_check_result(result)


def log_and_check_result(result):
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        # After running, there will be new commit
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


def get_incremental_dev_result(idea, project_name):
    project_path = TEST_DATA_PATH / "incremental_dev_project" / project_name
    if not os.path.exists(project_path):
        raise Exception(f"Project {project_name} not exists")
    check_or_create_base_tag(project_path)
    args = [
        idea,
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    return result


def check_or_create_base_tag(project_path):
    # Change the current working directory to the specified project path
    os.chdir(project_path)

    # Initialize a Git repository
    subprocess.run(["git", "init"], check=True)

    # Check if the 'base' tag exists
    check_base_tag_cmd = ["git", "show-ref", "--verify", "--quiet", "refs/tags/base"]
    if subprocess.run(check_base_tag_cmd).returncode == 0:
        has_base_tag = True
    else:
        has_base_tag = False

    if has_base_tag:
        logger.info("Base tag exists")
        # Switch to the 'base' branch if it exists
        try:
            status = subprocess.run(["git", "status", "-s"], capture_output=True, text=True).stdout.strip()
            if status:
                subprocess.run(["git", "clean", "-df"])
            subprocess.run(["git", "checkout", "-f", "base"], check=True)
            logger.info("Switched to base branch")
        except Exception as e:
            logger.error("Failed to switch to base branch")
            raise e

    else:
        logger.info("Base tag doesn't exist.")
        # Add and commit the current code if 'base' tag doesn't exist
        add_cmd = ["git", "add", "."]
        commit_cmd = ["git", "commit", "-m", "Initial commit"]
        try:
            subprocess.run(add_cmd, check=True)
            subprocess.run(commit_cmd, check=True)
            logger.info("Added and committed all files with the message 'Initial commit'.")
        except Exception as e:
            logger.error("Failed to add and commit all files.")
            raise e

        # Add 'base' tag
        add_base_tag_cmd = ["git", "tag", "base"]

        # Check if the 'git tag' command was successful
        try:
            subprocess.run(add_base_tag_cmd, check=True)
            logger.info("Added 'base' tag.")
        except Exception as e:
            logger.error("Failed to add 'base' tag.")
            raise e


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
