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
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


def test_refined_word_cloud():
    project_path = f"{DATA_PATH}/word_cloud"
    check_or_create_base_tag(project_path)

    args = [
        "Add a feature to remove deprecated words from the word cloud. The current word cloud generator does not support removing deprecated words. Now, The word cloud generator should support removing deprecated words. Customize deactivated words to exclude them from word cloud. Let users see all the words in the text file, and allow users to select the words they want to remove.",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


def test_refined_gomoku():
    project_path = f"{DATA_PATH}/Gomoku"
    check_or_create_base_tag(project_path)

    args = [
        "Add an AI opponent with fixed difficulty levels. Currently, the game only allows players to compete against themselves. Implement an AI algorithm that can playing with player. This will provide a more engaging and challenging experience for players.",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


def test_refined_dice_simulator_1():
    project_path = f"{DATA_PATH}/dice_simulator_new"
    check_or_create_base_tag(project_path)

    args = [
        "Add functionality to view the history of scores. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine_1"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


def test_refined_dice_simulator_2():
    project_path = f"{DATA_PATH}/dice_simulator_new"
    check_or_create_base_tag(project_path)

    args = [
        "Add functionality to view the history of scores and perform statistical analysis on them. The original dice rolling game could only display the current game result, but the new requirement allows players to view the history of scores and display the statistical analysis results of the current score",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine_2"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


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
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine_1"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


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
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine_2"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


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
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine_3"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


def test_refined_snake_game_1():
    project_path = f"{DATA_PATH}/snake_game"
    check_or_create_base_tag(project_path)

    args = [
        "Incremental Idea Gradually increase the speed of the snake as the game progresses. In the current version of the game, the snake’s speed remains constant throughout the gameplay. Implement a feature where the snake’s speed gradually increases over time, making the game more challenging and intense as the player progresses.",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine_1"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


def test_refined_snake_game_2():
    project_path = f"{DATA_PATH}/snake_game"
    check_or_create_base_tag(project_path)

    args = [
        "Introduce power-ups and obstacles to the game. The current version of the game only involves eating food and growing the snake. Add new elements such as power-ups that can enhance the snake’s speed or make it invincible for a short duration. At the same time, introduce obstacles like walls or enemies that the snake must avoid or overcome to continue growing.",
        "--inc",
        "--project-path",
        project_path,
    ]
    result = runner.invoke(app, args)
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if tag == "base":
            assert False
        else:
            assert True
            try:
                subprocess.run(["git", "tag", "refine_2"], check=True)
            except subprocess.CalledProcessError as e:
                raise e


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
