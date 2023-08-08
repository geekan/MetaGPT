#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:42
@Author  : alexanderwu
@File    : manager.py
"""
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.schema import Message


class Manager:
    def __init__(self, llm: LLM = LLM()):
        self.llm = llm  # Large Language Model
        self.role_directions = {
            "BOSS": "Product Manager",
            "Product Manager": "Architect",
            "Architect": "Engineer",
            "Engineer": "QA Engineer",
            "QA Engineer": "Product Manager"
        }
        self.prompt_template = """
        Given the following message:
        {message}

        And the current status of roles:
        {roles}

        Which role should handle this message?
        """

    async def handle(self, message: Message, environment):
        """
        管理员处理信息，现在简单的将信息递交给下一个人
        The administrator processes the information, now simply passes the information on to the next person
        :param message:
        :param environment:
        :return:
        """
        # Get all roles from the environment
        roles = environment.get_roles()
        # logger.debug(f"{roles=}, {message=}")

        # Build a context for the LLM to understand the situation
        # context = {
        #     "message": str(message),
        #     "roles": {role.name: role.get_info() for role in roles},
        # }
        # Ask the LLM to decide which role should handle the message
        # chosen_role_name = self.llm.ask(self.prompt_template.format(context))

        # FIXME: 现在通过简单的字典决定流向，但之后还是应该有思考过程
        #The direction of flow is now determined by a simple dictionary, but there should still be a thought process afterwards
        next_role_profile = self.role_directions[message.role]
        # logger.debug(f"{next_role_profile}")
        for _, role in roles.items():
            if next_role_profile == role.profile:
                next_role = role
                break
        else:
            logger.error(f"No available role can handle message: {message}.")
            return

        # Find the chosen role and handle the message
        return await next_role.handle(message)
