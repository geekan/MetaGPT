#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/7
@Author  : mashenquan
@File    : fork_meta_role.py
@Desc   : I am attempting to incorporate certain symbol concepts from UML into MetaGPT, enabling it to have the
            ability to freely construct flows through symbol concatenation. Simultaneously, I am also striving to
            make these symbols configurable and standardized, making the process of building flows more convenient.
            For more about `fork` node in activity diagrams, see: `https://www.uml-diagrams.org/activity-diagrams.html`
          This file defines a `fork` style meta role capable of generating arbitrary roles at runtime based on a
            configuration file.
"""

import re

import aiofiles

from metagpt.actions.meta_action import MetaAction
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.roles.uml_meta_role_options import MetaActionOptions, UMLMetaRoleOptions
from metagpt.schema import Message


class ForkMetaRole(Role):
    """A `fork` style meta role capable of generating arbitrary roles at runtime based on a configuration file"""
    def __init__(self, options, **kwargs):
        """Initialize a `fork` style meta role

        :param options: pattern yaml file data
        :param args: Parameters passed in format: `python your_script.py arg1 arg2 arg3`
        :param kwargs: Parameters passed in format: `python your_script.py --param1=value1 --param2=value2`
        """
        opts = UMLMetaRoleOptions(**options)
        global_variables = {
            "name": Role.format_value(opts.name, kwargs),
            "profile": Role.format_value(opts.profile, kwargs),
            "goal": Role.format_value(opts.goal, kwargs),
            "constraints": Role.format_value(opts.constraints, kwargs),
            "desc": Role.format_value(opts.desc, kwargs),
            "role": Role.format_value(opts.role, kwargs)
        }
        for k, v in kwargs.items():
            if k not in global_variables:
                global_variables[k] = v

        super(ForkMetaRole, self).__init__(
            name=global_variables["name"],
            profile=global_variables["profile"],
            goal=global_variables["goal"],
            constraints=global_variables["constraints"],
            desc=global_variables["desc"],
            **kwargs
        )
        self.options = options
        actions = []
        for m in opts.actions:
            for k, v in m.items():
                v = Role.format_value(v, kwargs)
                m[k] = v
            for k, v in global_variables.items():
                if k not in m:
                    m[k] = v

            o = MetaActionOptions(**m)
            o.set_default_template(opts.templates[o.template_ix])

            act = MetaAction(options=o, llm=self._llm, **m)
            actions.append(act)
        self._init_actions(actions)
        requirement_types = set()
        for v in opts.requirement:
            requirement_types.add(MetaAction.get_action_type(v))
        self._watch(requirement_types)

    async def _think(self) -> None:
        """Everything will be done part by part."""
        if self._rc.todo is None:
            self._set_state(0)
            return

        if self._rc.state + 1 < len(self._states):
            self._set_state(self._rc.state + 1)
        else:
            self._rc.todo = None

    async def _react(self) -> Message:
        ret = Message(content="")
        while True:
            await self._think()
            if self._rc.todo is None:
                break
            logger.debug(f"{self._setting}: {self._rc.state=}, will do {self._rc.todo}")
            msg = await self._act()
            if ret.content != '':
                ret.content += "\n\n\n"
            ret.content += msg.content
        logger.info(ret.content)
        await self.save(ret.content)
        return ret

    async def save(self, content):
        """Save teaching plan"""
        output_filename = self.options.get("output_filename")
        if not output_filename:
            return
        filename = ForkMetaRole.new_file_name(output_filename)
        pathname = WORKSPACE_ROOT / "teaching_plan"
        pathname.mkdir(exist_ok=True)
        pathname = pathname / filename
        try:
            async with aiofiles.open(str(pathname), mode='w', encoding='utf-8') as writer:
                await writer.write(content)
        except Exception as e:
            logger.error(f'Save failed：{e}')
        logger.info(f"Save to:{pathname}")

    @staticmethod
    def new_file_name(lesson_title, ext=".md"):
        """Create a related file name based on `lesson_title` and `ext`."""
        # Define the special characters that need to be replaced.
        illegal_chars = r'[#@$%!*&\\/:*?"<>|\n\t \']'
        # Replace the special characters with underscores.
        filename = re.sub(illegal_chars, '_', lesson_title) + ext
        return re.sub(r'_+', '_', filename)