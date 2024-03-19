#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_incremental_dev.py
"""
import os
import shutil
import subprocess
import time

import pytest
from typer.testing import CliRunner

from metagpt.const import TEST_DATA_PATH
from metagpt.logs import logger
from metagpt.software_company import app

runner = CliRunner()

IDEAS = [
    "Add subtraction, multiplication and division operations to the calculator. The current calculator can only perform basic addition operations, and it is necessary to introduce subtraction, multiplication, division operation into the calculator",
    "Adding graphical interface functionality to enhance the user experience in the number-guessing game. The existing number-guessing game currently relies on command-line input for numbers. The goal is to introduce a graphical interface to improve the game's usability and visual appeal",
    "Add a feature to remove deprecated words from the word cloud. The current word cloud generator does not support removing deprecated words. Now, The word cloud generator should support removing deprecated words. Customize deactivated words to exclude them from word cloud. Let users see all the words in the text file, and allow users to select the words they want to remove.",
    "Add an AI opponent with fixed difficulty levels. Currently, the game only allows players to compete against themselves. Implement an AI algorithm that can playing with player. This will provide a more engaging and challenging experience for players.",
    "Add functionality to view the history of scores. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores",
    "Add functionality to view the history of scores and perform statistical analysis on them. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores and display the statistical analysis results of the current score",
    "Changed score target for 2048 game from 2048 to 4096. Please change the game's score target from 2048 to 4096, and change the interface size from 4*4 to 8*8",
    "Display the history score of the player in the 2048 game. Add a record board that can display players' historical score records so that players can trace their scores",
    "Incremental Idea Gradually increase the speed of the snake as the game progresses. In the current version of the game, the snake’s speed remains constant throughout the gameplay. Implement a feature where the snake’s speed gradually increases over time, making the game more challenging and intense as the player progresses.",
    "Introduce power-ups and obstacles to the game. The current version of the game only involves eating food and growing the snake. Add new elements such as power-ups that can enhance the snake’s speed or make it invincible for a short duration. At the same time, introduce obstacles like walls or enemies that the snake must avoid or overcome to continue growing.",
]

PROJECT_NAMES = [
    "simple_add_calculator",
    "number_guessing_game",
    "word_cloud",
    "Gomoku",
    "dice_simulator_new",
    "dice_simulator_new",
    "pygame_2048",
    "pygame_2048",
    "snake_game",
    "snake_game",
]


@pytest.mark.skip
def test_simple_add_calculator():
    result = get_incremental_dev_result(IDEAS[0], PROJECT_NAMES[0])
    log_and_check_result(result)


@pytest.mark.skip
def test_number_guessing_game():
    result = get_incremental_dev_result(IDEAS[1], PROJECT_NAMES[1])
    log_and_check_result(result)


@pytest.mark.skip
def test_word_cloud():
    result = get_incremental_dev_result(IDEAS[2], PROJECT_NAMES[2])
    log_and_check_result(result)


@pytest.mark.skip
def test_gomoku():
    result = get_incremental_dev_result(IDEAS[3], PROJECT_NAMES[3])
    log_and_check_result(result)


@pytest.mark.skip
def test_dice_simulator_new():
    for i, (idea, project_name) in enumerate(zip(IDEAS[4:6], PROJECT_NAMES[4:6]), start=1):
        result = get_incremental_dev_result(idea, project_name)
        log_and_check_result(result, "refine_" + str(i))


@pytest.mark.skip
def test_refined_pygame_2048():
    for i, (idea, project_name) in enumerate(zip(IDEAS[6:8], PROJECT_NAMES[6:8]), start=1):
        result = get_incremental_dev_result(idea, project_name)
        log_and_check_result(result, "refine_" + str(i))


@pytest.mark.skip
def test_refined_snake_game():
    for i, (idea, project_name) in enumerate(zip(IDEAS[8:10], PROJECT_NAMES[8:10]), start=1):
        result = get_incremental_dev_result(idea, project_name)
        log_and_check_result(result, "refine_" + str(i))


def log_and_check_result(result, tag_name="refine"):
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        # After running, there will be new commit
        cur_tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if cur_tag == "base":
            assert False
        else:
            assert True
            if subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag_name}"]).returncode == 0:
                tag_name += str(int(time.time()))
            try:
                subprocess.run(["git", "tag", tag_name], check=True)
            except subprocess.CalledProcessError as e:
                raise e


def get_incremental_dev_result(idea, project_name, use_review=True):
    project_path = TEST_DATA_PATH / "incremental_dev_project" / project_name
    # Check if the project path exists
    if not project_path.exists():
        # If the project does not exist, extract the project file
        try:
            if shutil.which("unzip"):
                subprocess.run(["unzip", f"{project_path}.zip", "-d", str(project_path.parent)], check=True)
            elif shutil.which("tar"):
                subprocess.run(["tar", "-xf", f"{project_path}.zip", "-C", str(project_path.parent)], check=True)
            logger.info(f"Extracted project {project_name} successfully.")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Neither 'unzip' nor 'tar' command found. Error: {e}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract project {project_name}. Error: {e}")

    check_or_create_base_tag(project_path)
    args = [idea, "--inc", "--project-path", project_path, "--n-round", "20"]
    if not use_review:
        args.append("--no-code-review")
    result = runner.invoke(app, args)
    return result


def check_or_create_base_tag(project_path):
    # Change the current working directory to the specified project path
    os.chdir(project_path)

    # Initialize a Git repository
    subprocess.run(["git", "init"], check=True)

    # Check if the .gitignore exists. If it doesn't exist, create .gitignore and add the comment
    subprocess.run(f"echo # Ignore these files or directories > {'.gitignore'}", shell=True)

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
        try:
            subprocess.run(add_cmd, check=True)
            logger.info("Files added successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add files: {e}")

        commit_cmd = ["git", "commit", "-m", "Initial commit"]
        try:
            subprocess.run(commit_cmd, check=True)
            logger.info("Committed all files with the message 'Initial commit'.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e.stderr}")

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
