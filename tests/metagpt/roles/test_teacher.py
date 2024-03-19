#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/27 13:25
@Author  : mashenquan
@File    : test_teacher.py
"""
from typing import Dict, Optional

import pytest
from pydantic import BaseModel, Field

from metagpt.context import Context
from metagpt.roles.teacher import Teacher
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_init():
    class Inputs(BaseModel):
        name: str
        profile: str
        goal: str
        constraints: str
        desc: str
        kwargs: Optional[Dict] = None
        expect_name: str
        expect_profile: str
        expect_goal: str
        expect_constraints: str
        expect_desc: str
        exclude: list = Field(default_factory=list)

    inputs = [
        {
            "name": "Lily{language}",
            "expect_name": "Lily{language}",
            "profile": "X {teaching_language}",
            "expect_profile": "X {teaching_language}",
            "goal": "Do {something_big}, {language}",
            "expect_goal": "Do {something_big}, {language}",
            "constraints": "Do in {key1}, {language}",
            "expect_constraints": "Do in {key1}, {language}",
            "kwargs": {},
            "desc": "aaa{language}",
            "expect_desc": "aaa{language}",
            "exclude": ["language", "key1", "something_big", "teaching_language"],
        },
        {
            "name": "Lily{language}",
            "expect_name": "LilyCN",
            "profile": "X {teaching_language}",
            "expect_profile": "X EN",
            "goal": "Do {something_big}, {language}",
            "expect_goal": "Do sleep, CN",
            "constraints": "Do in {key1}, {language}",
            "expect_constraints": "Do in HaHa, CN",
            "kwargs": {"language": "CN", "key1": "HaHa", "something_big": "sleep", "teaching_language": "EN"},
            "desc": "aaa{language}",
            "expect_desc": "aaaCN",
            "language": "CN",
            "teaching_language": "EN",
        },
    ]

    for i in inputs:
        seed = Inputs(**i)
        context = Context()
        for k in seed.exclude:
            context.kwargs.set(k, None)
        for k, v in seed.kwargs.items():
            context.kwargs.set(k, v)

        teacher = Teacher(
            context=context,
            name=seed.name,
            profile=seed.profile,
            goal=seed.goal,
            constraints=seed.constraints,
            desc=seed.desc,
        )
        assert teacher.name == seed.expect_name
        assert teacher.desc == seed.expect_desc
        assert teacher.profile == seed.expect_profile
        assert teacher.goal == seed.expect_goal
        assert teacher.constraints == seed.expect_constraints
        assert teacher.course_title == "teaching_plan"


@pytest.mark.asyncio
async def test_new_file_name():
    class Inputs(BaseModel):
        lesson_title: str
        ext: str
        expect: str

    inputs = [
        {"lesson_title": "# @344\n12", "ext": ".md", "expect": "_344_12.md"},
        {"lesson_title": "1#@$%!*&\\/:*?\"<>|\n\t '1", "ext": ".cc", "expect": "1_1.cc"},
    ]
    for i in inputs:
        seed = Inputs(**i)
        result = Teacher.new_file_name(seed.lesson_title, seed.ext)
        assert result == seed.expect


@pytest.mark.asyncio
async def test_run():
    lesson = """
    UNIT 1 Making New Friends
    TOPIC 1 Welcome to China!
    Section A

    1a Listen and number the following names.
    Jane Mari Kangkang Michael
    Look, listen and understand. Then practice the conversation.
    Work in groups. Introduce yourself using
    I ’m ... Then practice 1a
    with your own hometown or the following places.

    1b Listen and number the following names
    Jane Michael Maria Kangkang
    1c Work in groups. Introduce yourself using I ’m ... Then practice 1a with your own hometown or the following places.
    China the USA the UK Hong Kong Beijing

    2a Look, listen and understand. Then practice the conversation
    Hello! 
    Hello! 
    Hello! 
    Hello! Are you Maria? 
    No, I’m not. I’m Jane.
    Oh, nice to meet you, Jane
    Nice to meet you, too.
    Hi, Maria!
    Hi, Kangkang!
    Welcome to China!
    Thanks.

    2b Work in groups. Make up a conversation with your own name and the
    following structures.
    A: Hello! / Good morning! / Hi! I’m ... Are you ... ?
    B: ...

    3a Listen, say and trace
    Aa Bb Cc Dd Ee Ff Gg

    3b Listen and number the following letters. Then circle the letters with the same sound as Bb.
    Aa Bb Cc Dd Ee Ff Gg

    3c Match the big letters with the small ones. Then write them on the lines.
    """
    context = Context()
    context.kwargs.language = "Chinese"
    context.kwargs.teaching_language = "English"
    teacher = Teacher(context=context)
    rsp = await teacher.run(Message(content=lesson))
    assert rsp


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
