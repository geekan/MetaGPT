#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import fire
import yaml

from metagpt.roles import Architect, Engineer, ProductManager, ProjectManager
from metagpt.software_company import SoftwareCompany


def read_config(filename):
    with open(filename, 'r') as file:
        config_data = yaml.safe_load(file)
    return config_data


def instantiate_class(item, **options):
    if isinstance(item, str):
        # If item is a string, instantiate the class directly
        class_obj = globals().get(item)
        if class_obj is None:
            raise ValueError(f"Class '{item}' not found in the global namespace.")
        return class_obj()
    elif isinstance(item, dict):
        # If item is a dictionary, it should contain class name and params
        class_name, params = next(iter(item.items()))
        if isinstance(params, dict):
            # Process the parameters based on the options
            for key, value in params.items():
                if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                    param_key = value.strip("{}")
                    params[key] = options.get(param_key, value)  # Use the option value or keep the original string
        class_obj = globals().get(class_name)
        if class_obj is None:
            raise ValueError(f"Class '{class_name}' not found in the global namespace.")
        return class_obj(**params)
    else:
        raise ValueError("Invalid item in team_config_1['team']. Each item should be a string or a dictionary.")


async def startup(idea: str, investment: float = 3.0, n_round: int = 5, code_review: bool = False):
    """Run a startup. Be a boss."""
    company = SoftwareCompany()
    # company.hire([ProductManager(),
    #               Architect(),
    #               ProjectManager(),
    #               Engineer(n_borg=5, use_code_review=code_review)])
    team_config = read_config('team_config.yaml')
    # Instantiate classes from the class names provided in team_config
    team = [instantiate_class(item, idea=idea, investment=investment, n_round=n_round, code_review=code_review) for item in team_config['team']]

    company.hire(team)
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


def main(idea: str, investment: float = 3.0, n_round: int = 5, code_review: bool = False):
    """
    We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.
    :param idea: Your innovative idea, such as "Creating a snake game."
    :param investment: As an investor, you have the opportunity to contribute a certain dollar amount to this AI company.
    :param n_round:
    :param code_review: Whether to use code review.
    :return:
    """
    asyncio.run(startup(idea, investment, n_round, code_review))


if __name__ == '__main__':
    fire.Fire(main)
