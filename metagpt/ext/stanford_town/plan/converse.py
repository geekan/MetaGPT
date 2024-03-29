#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : conversation between two agents

from typing import Tuple

from metagpt.ext.stanford_town.actions.agent_chat_sum_rel import AgentChatSumRel
from metagpt.ext.stanford_town.actions.gen_iter_chat_utt import GenIterChatUTT
from metagpt.ext.stanford_town.memory.retrieve import new_agent_retrieve
from metagpt.logs import logger


async def agent_conversation(init_role: "STRole", target_role: "STRole", conv_rounds: int = 8) -> list[list[str]]:
    curr_chat = []
    logger.info(f"Role: {init_role.name} starts a conversation with Role: {target_role.name}")

    for idx in range(conv_rounds):
        logger.info(f"Conv round: {idx} between {init_role.name} and {target_role.name}")
        scratch = init_role.rc.scratch
        target_scratch = target_role.rc.scratch

        focal_points = [f"{target_scratch.name}"]
        retrieved = new_agent_retrieve(init_role, focal_points, 50)
        relationship = await generate_summarize_agent_relationship(init_role, target_role, retrieved)
        logger.info(f"The relationship between {init_role.name} and {target_role.name}: {relationship}")
        last_chat = ""
        for i in curr_chat[-4:]:
            last_chat += ": ".join(i) + "\n"
        if last_chat:
            focal_points = [f"{relationship}", f"{target_scratch.name} is {target_scratch.act_description}", last_chat]
        else:
            focal_points = [f"{relationship}", f"{target_scratch.name} is {target_scratch.act_description}"]
        retrieved = new_agent_retrieve(init_role, focal_points, 15)
        utt, end = await generate_one_utterance(init_role, target_role, retrieved, curr_chat)

        curr_chat += [[scratch.name, utt]]
        if end:
            break

        focal_points = [f"{scratch.name}"]
        retrieved = new_agent_retrieve(target_role, focal_points, 50)
        relationship = await generate_summarize_agent_relationship(target_role, init_role, retrieved)
        logger.info(f"The relationship between {target_role.name} and {init_role.name}: {relationship}")
        last_chat = ""
        for i in curr_chat[-4:]:
            last_chat += ": ".join(i) + "\n"
        if last_chat:
            focal_points = [f"{relationship}", f"{scratch.name} is {scratch.act_description}", last_chat]
        else:
            focal_points = [f"{relationship}", f"{scratch.name} is {scratch.act_description}"]
        retrieved = new_agent_retrieve(target_role, focal_points, 15)
        utt, end = await generate_one_utterance(target_role, init_role, retrieved, curr_chat)

        curr_chat += [[target_scratch.name, utt]]
        if end:
            break

    logger.warning(f"Conversations between {target_role.name} and {init_role.name}:")
    for row in curr_chat:
        logger.info(row)

    return curr_chat


async def generate_summarize_agent_relationship(init_role: "STRole", target_role: "STRole", retrieved: dict) -> str:
    all_embedding_keys = list()
    for key, val in retrieved.items():
        for i in val:
            all_embedding_keys += [i.embedding_key]
    all_embedding_key_str = ""
    for i in all_embedding_keys:
        all_embedding_key_str += f"{i}\n"

    summarized_relationship = await AgentChatSumRel().run(init_role, target_role, all_embedding_key_str)
    return summarized_relationship


async def generate_one_utterance(init_role, target_role, retrieved: dict, curr_chat: list) -> Tuple[str, str]:
    # Chat version optimized for speed via batch generation
    scratch = init_role.rc.scratch
    target_scratch = target_role.rc.scratch
    curr_context = (
        f"{scratch.name} "
        + f"was {scratch.act_description} "
        + f"when {scratch.name} "
        + f"saw {target_scratch.name} "
        + f"in the middle of {target_scratch.act_description}.\n"
    )
    curr_context += f"{scratch.name} " + "is initiating a conversation with " + f"{target_scratch.name}."

    x = await GenIterChatUTT().run(init_role, target_role, retrieved, curr_context, curr_chat)

    return x["utterance"], x["end"]
