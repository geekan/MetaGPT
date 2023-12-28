#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/6 12:38
@Author  : alexanderwu
@File    : test_skill_manager.py
"""
from metagpt.actions import WritePRD, WriteTest
from metagpt.logs import logger
from metagpt.management.skill_manager import SkillManager


def test_skill_manager():
    manager = SkillManager()
    logger.info(manager._store)

    write_prd = WritePRD(name="WritePRD")
    write_prd.desc = "基于老板或其他人的需求进行PRD的撰写，包括用户故事、需求分解等"
    write_test = WriteTest(name="WriteTest")
    write_test.desc = "进行测试用例的撰写"
    manager.add_skill(write_prd)
    manager.add_skill(write_test)

    skill = manager.get_skill("WriteTest")
    logger.info(skill)

    rsp = manager.retrieve_skill("WritePRD")
    logger.info(rsp)
    assert rsp[0] == "WritePRD"

    rsp = manager.retrieve_skill("写测试用例")
    logger.info(rsp)
    assert rsp[0] == "WriteTest"

    rsp = manager.retrieve_skill_scored("写PRD")
    logger.info(rsp)
