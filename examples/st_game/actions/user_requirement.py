#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from metagpt.actions import Action


class UserRequirement(Action):

    async def run(self, *args, **kwargs):
        raise NotImplementedError
