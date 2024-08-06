#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : st' planning execution

import datetime
import math
import random
from typing import Tuple, Union

from metagpt.ext.stanford_town.actions.decide_to_talk import DecideToTalk
from metagpt.ext.stanford_town.actions.gen_action_details import GenActionDetails
from metagpt.ext.stanford_town.actions.gen_daily_schedule import GenDailySchedule
from metagpt.ext.stanford_town.actions.gen_hourly_schedule import GenHourlySchedule
from metagpt.ext.stanford_town.actions.new_decomp_schedule import NewDecompSchedule
from metagpt.ext.stanford_town.actions.summarize_conv import SummarizeConv
from metagpt.ext.stanford_town.actions.task_decomp import TaskDecomp
from metagpt.ext.stanford_town.actions.wake_up import WakeUp
from metagpt.ext.stanford_town.memory.retrieve import new_agent_retrieve
from metagpt.ext.stanford_town.plan.converse import agent_conversation
from metagpt.ext.stanford_town.utils.utils import get_embedding
from metagpt.llm import LLM
from metagpt.logs import logger


async def plan(role: "STRole", roles: dict["STRole"], new_day: bool, retrieved: dict) -> str:
    # PART 1: Generate the hourly schedule.
    if new_day:
        await _long_term_planning(role, new_day)

    # PART 2: If the current action has expired, we want to create a new plan.
    act_check_finished = role.scratch.act_check_finished()
    logger.info(f"Role: {role.name} act_check_finished is {act_check_finished}")
    if act_check_finished:
        await _determine_action(role)

    # PART 3: If you perceived an event that needs to be responded to (saw
    # another role), and retrieved relevant information.
    # Step 1: Retrieved may have multiple events represented in it. The first
    #         job here is to determine which of the events we want to focus
    #         on for the role.
    #         <focused_event> takes the form of a dictionary like this:
    #         dictionary {["curr_event"] = <ConceptNode>,
    #                     ["events"] = [<ConceptNode>, ...],
    #                     ["thoughts"] = [<ConceptNode>, ...]}
    focused_event = False
    if retrieved.keys():
        focused_event = _choose_retrieved(role.name, retrieved)

    # Step 2: Once we choose an event, we need to determine whether the
    #         role will take any actions for the perceived event. There are
    #         three possible modes of reaction returned by _should_react.
    #         a) "chat with {target_role.name}"
    #         b) "react"
    #         c) False
    logger.info(f"Role: {role.name} focused_event: {focused_event}")
    if focused_event:
        reaction_mode = await _should_react(role, focused_event, roles)
        logger.info(f"Role: {role.name} reaction_mode: {reaction_mode}")
        if reaction_mode:
            # If we do want to chat, then we generate conversation
            if reaction_mode[:9] == "chat with":
                await _chat_react(role, reaction_mode, roles)
            elif reaction_mode[:4] == "wait":
                await _wait_react(role, reaction_mode)

    # Step 3: Chat-related state clean up.
    # If the persona is not chatting with anyone, we clean up any of the
    # chat-related states here.
    if role.rc.scratch.act_event[1] != "chat with":
        role.rc.scratch.chatting_with = None
        role.rc.scratch.chat = None
        role.rc.scratch.chatting_end_time = None
    # We want to make sure that the persona does not keep conversing with each
    # other in an infinite loop. So, chatting_with_buffer maintains a form of
    # buffer that makes the persona wait from talking to the same target
    # immediately after chatting once. We keep track of the buffer value here.
    curr_persona_chat_buffer = role.rc.scratch.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != role.rc.scratch.chatting_with:
            role.rc.scratch.chatting_with_buffer[persona_name] -= 1

    return role.rc.scratch.act_address


def _choose_retrieved(role_name: str, retrieved: dict) -> Union[None, dict]:
    """
    Retrieved elements have multiple core "curr_events". We need to choose one
    event to which we are going to react to. We pick that event here.
    Args:
      role_name: Current role instance's name whose action we are determining.
      retrieved: A dictionary of <ConceptNode> that were retrieved from the
                 the role's associative memory. This dictionary takes the
                 following form:
                 dictionary[event.description] =
                   {["curr_event"] = <ConceptNode>,
                    ["events"] = [<ConceptNode>, ...],
                    ["thoughts"] = [<ConceptNode>, ...] }
    """
    # Once we are done with the reflection, we might want to build a more
    # complex structure here.

    # We do not want to take self events... for now
    copy_retrieved = retrieved.copy()
    for event_desc, rel_ctx in copy_retrieved.items():
        curr_event = rel_ctx["curr_event"]
        if curr_event.subject == role_name:
            del retrieved[event_desc]

    # Always choose role first.
    priority = []
    for event_desc, rel_ctx in retrieved.items():
        curr_event = rel_ctx["curr_event"]
        if ":" not in curr_event.subject and curr_event.subject != role_name:
            priority += [rel_ctx]
    if priority:
        return random.choice(priority)

    # Skip idle.
    for event_desc, rel_ctx in retrieved.items():
        if "is idle" not in event_desc:
            priority += [rel_ctx]
    if priority:
        return random.choice(priority)
    return None


async def _should_react(role: "STRole", retrieved: dict, roles: dict):
    """
    Determines what form of reaction the role should exihibit given the
    retrieved values.
    INPUT
      role: Current <"STRole"> instance whose action we are determining.
      retrieved: A dictionary of <ConceptNode> that were retrieved from the
                 the role's associative memory. This dictionary takes the
                 following form:
                 dictionary[event.description] =
                   {["curr_event"] = <ConceptNode>,
                    ["events"] = [<ConceptNode>, ...],
                    ["thoughts"] = [<ConceptNode>, ...] }
      roles: A dictionary that contains all role names as keys, and the
                <"STRole"> instance as values.
    """

    async def lets_talk(init_role: "STRole", target_role: "STRole", retrieved: dict):
        if init_role.name == target_role.name:
            logger.info(f"Role: {role.name} _should_react lets_talk meet same role, return False")
            return False

        scratch = init_role.rc.scratch
        target_scratch = target_role.rc.scratch
        if (
            not target_scratch.act_address
            or not target_scratch.act_description
            or not scratch.act_address
            or not scratch.act_description
        ):
            return False

        if "sleeping" in target_scratch.act_description or "sleeping" in scratch.act_description:
            return False

        if scratch.curr_time.hour == 23:
            return False

        if "<waiting>" in target_scratch.act_address:
            return False

        if target_scratch.chatting_with or scratch.chatting_with:
            return False

        if target_role.name in scratch.chatting_with_buffer:
            if scratch.chatting_with_buffer[target_role.name] > 0:
                return False

        if await DecideToTalk().run(init_role, target_role, retrieved):
            return True

        return False

    async def lets_react(init_role: "STRole", target_role: "STRole", retrieved: dict):
        if init_role.name == target_role.name:
            logger.info(f"Role: {role.name} _should_react lets_react meet same role, return False")
            return False

        scratch = init_role.rc.scratch
        target_scratch = target_role.rc.scratch
        if (
            not target_scratch.act_address
            or not target_scratch.act_description
            or not scratch.act_address
            or not scratch.act_description
        ):
            return False

        if "sleeping" in target_scratch.act_description or "sleeping" in scratch.act_description:
            return False

        # return False
        if scratch.curr_time.hour == 23:
            return False

        if "waiting" in target_scratch.act_description:
            return False
        if scratch.planned_path == []:
            return False

        if scratch.act_address != target_scratch.act_address:
            return False

        react_mode = await DecideToTalk().run(init_role, target_role, retrieved)

        if react_mode == "1":
            wait_until = (
                target_scratch.act_start_time + datetime.timedelta(minutes=target_scratch.act_duration - 1)
            ).strftime("%B %d, %Y, %H:%M:%S")
            return f"wait: {wait_until}"
        elif react_mode == "2":
            return False
            return "do other things"
        else:
            return False  # "keep"

    # If the role is chatting right now, default to no reaction
    scratch = role.rc.scratch
    if scratch.chatting_with:
        return False
    if "<waiting>" in scratch.act_address:
        return False

    # Recall that retrieved takes the following form:
    # dictionary {["curr_event"] = <ConceptNode>}
    curr_event = retrieved["curr_event"]
    logger.info(f"Role: {role.name} _should_react curr_event.subject: {curr_event.subject}")

    if ":" not in curr_event.subject:
        # this is a role event.
        if await lets_talk(role, roles[curr_event.subject], retrieved):
            return f"chat with {curr_event.subject}"
        react_mode = await lets_react(role, roles[curr_event.subject], retrieved)
        return react_mode
    return False


async def _chat_react(role: "STRole", reaction_mode: str, roles: dict["STRole"]):
    # There are two roles -- the role who is initiating the conversation
    # and the role who is the target. We get the role instances here.
    init_role = role
    target_role = roles[reaction_mode[9:].strip()]

    # Actually creating the conversation here.
    convo, duration_min = await generate_convo(init_role, target_role)  # 2222
    convo_summary = await generate_convo_summary(convo)
    inserted_act = convo_summary
    inserted_act_dur = duration_min

    act_start_time = target_role.rc.scratch.act_start_time

    curr_time = target_role.rc.scratch.curr_time
    if curr_time.second != 0:
        temp_curr_time = curr_time + datetime.timedelta(seconds=60 - curr_time.second)
        chatting_end_time = temp_curr_time + datetime.timedelta(minutes=inserted_act_dur)
    else:
        chatting_end_time = curr_time + datetime.timedelta(minutes=inserted_act_dur)

    for role, p in [("init", init_role), ("target", target_role)]:
        if role == "init":
            act_address = f"<persona> {target_role.name}"
            act_event = (p.name, "chat with", target_role.name)
            chatting_with = target_role.name
            chatting_with_buffer = {}
            chatting_with_buffer[target_role.name] = 800
        elif role == "target":
            act_address = f"<persona> {init_role.name}"
            act_event = (p.name, "chat with", init_role.name)
            chatting_with = init_role.name
            chatting_with_buffer = {}
            chatting_with_buffer[init_role.name] = 800

        act_pronunciatio = "💬"
        act_obj_description = None
        act_obj_pronunciatio = None
        act_obj_event = (None, None, None)

        await _create_react(
            p,
            inserted_act,
            inserted_act_dur,
            act_address,
            act_event,
            chatting_with,
            convo,
            chatting_with_buffer,
            chatting_end_time,
            act_pronunciatio,
            act_obj_description,
            act_obj_pronunciatio,
            act_obj_event,
            act_start_time,
        )


async def _create_react(
    role: "STRole",
    inserted_act: str,
    inserted_act_dur: int,
    act_address: str,
    act_event: Tuple,
    chatting_with: str,
    chat: list,
    chatting_with_buffer: dict,
    chatting_end_time: datetime,
    act_pronunciatio: str,
    act_obj_description: str,
    act_obj_pronunciatio: str,
    act_obj_event: Tuple,
    act_start_time=None,
):
    p = role
    scratch = role.rc.scratch

    min_sum = 0
    for i in range(scratch.get_f_daily_schedule_hourly_org_index()):
        min_sum += scratch.f_daily_schedule_hourly_org[i][1]
    start_hour = int(min_sum / 60)

    if scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1] >= 120:
        end_hour = (
            start_hour + scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1] / 60
        )

    elif (
        scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1]
        + scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index() + 1][1]
    ):
        end_hour = start_hour + (
            (
                scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1]
                + scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index() + 1][1]
            )
            / 60
        )

    else:
        end_hour = start_hour + 2
    end_hour = int(end_hour)

    dur_sum = 0
    count = 0
    start_index = None
    end_index = None
    for act, dur in scratch.f_daily_schedule:
        if dur_sum >= start_hour * 60 and start_index is None:
            start_index = count
        if dur_sum >= end_hour * 60 and end_index is None:
            end_index = count
        dur_sum += dur
        count += 1

    ret = await generate_new_decomp_schedule(p, inserted_act, inserted_act_dur, start_hour, end_hour)
    scratch.f_daily_schedule[start_index:end_index] = ret
    scratch.add_new_action(
        act_address,
        inserted_act_dur,
        inserted_act,
        act_pronunciatio,
        act_event,
        chatting_with,
        chat,
        chatting_with_buffer,
        chatting_end_time,
        act_obj_description,
        act_obj_pronunciatio,
        act_obj_event,
        act_start_time,
    )


async def _wait_react(role: "STRole", reaction_mode: str):
    scratch = role.rc.scratch

    inserted_act = f'waiting to start {scratch.act_description.split("(")[-1][:-1]}'
    end_time = datetime.datetime.strptime(reaction_mode[6:].strip(), "%B %d, %Y, %H:%M:%S")
    inserted_act_dur = (
        (end_time.minute + end_time.hour * 60) - (scratch.curr_time.minute + scratch.curr_time.hour * 60) + 1
    )

    act_address = f"<waiting> {scratch.curr_tile[0]} {scratch.curr_tile[1]}"
    act_event = (role.name, "waiting to start", scratch.act_description.split("(")[-1][:-1])
    chatting_with = None
    chat = None
    chatting_with_buffer = None
    chatting_end_time = None

    act_pronunciatio = "⌛"
    act_obj_description = None
    act_obj_pronunciatio = None
    act_obj_event = (None, None, None)

    await _create_react(
        role,
        inserted_act,
        inserted_act_dur,
        act_address,
        act_event,
        chatting_with,
        chat,
        chatting_with_buffer,
        chatting_end_time,
        act_pronunciatio,
        act_obj_description,
        act_obj_pronunciatio,
        act_obj_event,
    )


async def generate_convo(init_role: "STRole", target_role: "STRole") -> Union[list, int]:
    convo = await agent_conversation(init_role, target_role)
    all_utt = ""

    for row in convo:
        speaker = row[0]
        utt = row[1]
        all_utt += f"{speaker}: {utt}\n"

    convo_length = math.ceil(int(len(all_utt) / 8) / 30)

    return convo, convo_length


async def generate_convo_summary(conv: list[list[str]]) -> str:
    conv_summary = await SummarizeConv().run(conv)
    return conv_summary


async def generate_new_decomp_schedule(
    role: "STRole", inserted_act: str, inserted_act_dur: int, start_hour: int, end_hour: int
):
    # Step 1: Setting up the core variables for the function.
    # <p> is the role whose schedule we are editing right now.
    scratch = role.rc.scratch
    # <today_min_pass> indicates the number of minutes that have passed today.
    today_min_pass = int(scratch.curr_time.hour) * 60 + int(scratch.curr_time.minute) + 1

    # Step 2: We need to create <main_act_dur> and <truncated_act_dur>.
    main_act_dur = []
    truncated_act_dur = []
    dur_sum = 0  # duration sum
    count = 0  # enumerate count
    truncated_fin = False

    logger.debug(f"DEBUG::: {scratch.name}")
    for act, dur in scratch.f_daily_schedule:
        if (dur_sum >= start_hour * 60) and (dur_sum < end_hour * 60):
            main_act_dur += [[act, dur]]
            if dur_sum <= today_min_pass:
                truncated_act_dur += [[act, dur]]
            elif dur_sum > today_min_pass and not truncated_fin:
                # We need to insert that last act, duration list like this one:
                # e.g., ['wakes up and completes her morning routine (wakes up...)', 2]
                truncated_act_dur += [[scratch.f_daily_schedule[count][0], dur_sum - today_min_pass]]
                truncated_act_dur[-1][-1] -= (
                    dur_sum - today_min_pass
                )  # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass + 1)
                logger.debug(f"DEBUG::: {truncated_act_dur}")

                # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass)
                truncated_fin = True
        dur_sum += dur
        count += 1

    main_act_dur = main_act_dur

    x = (
        truncated_act_dur[-1][0].split("(")[0].strip()
        + " (on the way to "
        + truncated_act_dur[-1][0].split("(")[-1][:-1]
        + ")"
    )
    truncated_act_dur[-1][0] = x

    if "(" in truncated_act_dur[-1][0]:
        inserted_act = truncated_act_dur[-1][0].split("(")[0].strip() + " (" + inserted_act + ")"

    # To do inserted_act_dur+1 below is an important decision but I'm not sure
    # if I understand the full extent of its implications. Might want to
    # revisit.
    truncated_act_dur += [[inserted_act, inserted_act_dur]]
    start_time_hour = datetime.datetime(2022, 10, 31, 0, 0) + datetime.timedelta(hours=start_hour)
    end_time_hour = datetime.datetime(2022, 10, 31, 0, 0) + datetime.timedelta(hours=end_hour)

    return await NewDecompSchedule().run(
        role, main_act_dur, truncated_act_dur, start_time_hour, end_time_hour, inserted_act, inserted_act_dur
    )


async def _long_term_planning(role: "STRole", new_day: bool):
    """
    Formulates the role's daily long-term plan if it is the start of a new
    day. This basically has two components: first, we create the wake-up hour,
    and second, we create the hourly schedule based on it.
    INPUT
        new_day: Indicates whether the current time signals a "First day",
                "New day", or False (for neither). This is important because we
                create the roles' long term planning on the new day.
    """
    # We start by creating the wake up hour for the role.
    wake_up_hour = await WakeUp().run(role)
    wake_up_hour = int(wake_up_hour)
    logger.info(f"Role: {role.name} long_term_planning, wake_up_hour: {wake_up_hour}")

    # When it is a new day, we start by creating the daily_req of the role.
    # Note that the daily_req is a list of strings that describe the role's
    # day in broad strokes.
    if new_day == "First day":
        # Bootstrapping the daily plan for the start of then generation:
        # if this is the start of generation (so there is no previous day's
        # daily requirement, or if we are on a new day, we want to create a new
        # set of daily requirements.
        role.scratch.daily_req = await GenDailySchedule().run(role, wake_up_hour)
        logger.info(f"Role: {role.name} daily requirements: {role.scratch.daily_req}")
    elif new_day == "New day":
        revise_identity(role)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - TODO
        # We need to create a new daily_req here...
        role.scratch.daily_req = role.scratch.daily_req

    # Based on the daily_req, we create an hourly schedule for the role,
    # which is a list of todo items with a time duration (in minutes) that
    # add up to 24 hours.
    role.scratch.f_daily_schedule = await GenHourlySchedule().run(role, wake_up_hour)
    logger.info(f"Role: {role.name} f_daily_schedule: {role.scratch.f_daily_schedule}")
    role.scratch.f_daily_schedule_hourly_org = role.scratch.f_daily_schedule[:]

    # Added March 4 -- adding plan to the memory.
    thought = f"This is {role.scratch.name}'s plan for {role.scratch.curr_time.strftime('%A %B %d')}:"
    for i in role.scratch.daily_req:
        thought += f" {i},"
    thought = thought[:-1] + "."
    created = role.scratch.curr_time
    expiration = role.scratch.curr_time + datetime.timedelta(days=30)
    s, p, o = (role.scratch.name, "plan", role.scratch.curr_time.strftime("%A %B %d"))
    keywords = set(["plan"])
    thought_poignancy = 5
    thought_embedding_pair = (thought, get_embedding(thought))
    role.a_mem.add_thought(
        created, expiration, s, p, o, thought, keywords, thought_poignancy, thought_embedding_pair, None
    )


async def _determine_action(role: "STRole"):
    """
    Creates the next action sequence for the role.
    The main goal of this function is to run "add_new_action" on the role's
    scratch space, which sets up all the action related variables for the next
    action.
    As a part of this, the role may need to decompose its hourly schedule as
    needed.
    INPUT
        role: Current <Persona> instance whose action we are determining.
    """

    def determine_decomp(act_desp, act_dura):
        """
        Given an action description and its duration, we determine whether we need
        to decompose it. If the action is about the agent sleeping, we generally
        do not want to decompose it, so that's what we catch here.

        INPUT:
        act_desp: the description of the action (e.g., "sleeping")
        act_dura: the duration of the action in minutes.
        OUTPUT:
        a boolean. True if we need to decompose, False otherwise.
        """
        if "sleep" not in act_desp and "bed" not in act_desp:
            return True
        elif "sleeping" in act_desp or "asleep" in act_desp or "in bed" in act_desp:
            return False
        elif "sleep" in act_desp or "bed" in act_desp:
            if act_dura > 60:
                return False
        return True

    # The goal of this function is to get us the action associated with
    # <curr_index>. As a part of this, we may need to decompose some large
    # chunk actions.
    # Importantly, we try to decompose at least two hours worth of schedule at
    # any given point.
    curr_index = role.scratch.get_f_daily_schedule_index()
    curr_index_60 = role.scratch.get_f_daily_schedule_index(advance=60)

    logger.info(f"f_daily_schedule: {role.scratch.f_daily_schedule}")
    # * Decompose *
    # During the first hour of the day, we need to decompose two hours
    # sequence. We do that here.
    if curr_index == 0:
        # This portion is invoked if it is the first hour of the day.
        act_desp, act_dura = role.scratch.f_daily_schedule[curr_index]
        if act_dura >= 60:
            # We decompose if the next action is longer than an hour, and fits the
            # criteria described in determine_decomp.
            if determine_decomp(act_desp, act_dura):
                role.scratch.f_daily_schedule[curr_index : curr_index + 1] = await TaskDecomp().run(
                    role, act_desp, act_dura
                )
        if curr_index_60 + 1 < len(role.scratch.f_daily_schedule):
            act_desp, act_dura = role.scratch.f_daily_schedule[curr_index_60 + 1]
            if act_dura >= 60:
                if determine_decomp(act_desp, act_dura):
                    role.scratch.f_daily_schedule[curr_index_60 + 1 : curr_index_60 + 2] = await TaskDecomp().run(
                        role, act_desp, act_dura
                    )

    if curr_index_60 < len(role.scratch.f_daily_schedule):
        # If it is not the first hour of the day, this is always invoked (it is
        # also invoked during the first hour of the day -- to double up so we can
        # decompose two hours in one go). Of course, we need to have something to
        # decompose as well, so we check for that too.
        if role.scratch.curr_time.hour < 23:
            # And we don't want to decompose after 11 pm.
            act_desp, act_dura = role.scratch.f_daily_schedule[curr_index_60]
            if act_dura >= 60:
                if determine_decomp(act_desp, act_dura):
                    role.scratch.f_daily_schedule[curr_index_60 : curr_index_60 + 1] = await TaskDecomp().run(
                        role, act_desp, act_dura
                    )
    # * End of Decompose *

    # Generate an <Action> instance from the action description and duration. By
    # this point, we assume that all the relevant actions are decomposed and
    # ready in f_daily_schedule.
    logger.debug("DEBUG LJSDLFSKJF")
    for i in role.scratch.f_daily_schedule:
        logger.debug(i)
    logger.debug(curr_index)
    logger.debug(len(role.scratch.f_daily_schedule))
    logger.debug(role.scratch.name)

    # 1440
    x_emergency = 0
    for i in role.scratch.f_daily_schedule:
        x_emergency += i[1]

    if 1440 - x_emergency > 0:
        logger.info(f"x_emergency__AAA: {x_emergency}")
    role.scratch.f_daily_schedule += [["sleeping", 1440 - x_emergency]]

    act_desp, act_dura = role.scratch.f_daily_schedule[curr_index]

    new_action_details = await GenActionDetails().run(role, act_desp, act_dura)
    # Adding the action to role's queue.
    role.scratch.add_new_action(**new_action_details)


def revise_identity(role: "STRole"):
    p_name = role.scratch.name

    focal_points = [
        f"{p_name}'s plan for {role.scratch.get_str_curr_date_str()}.",
        f"Important recent events for {p_name}'s life.",
    ]
    retrieved = new_agent_retrieve(role, focal_points)

    statements = "[Statements]\n"
    for key, val in retrieved.items():
        for i in val:
            statements += f"{i.created.strftime('%A %B %d -- %H:%M %p')}: {i.embedding_key}\n"

    plan_prompt = statements + "\n"
    plan_prompt += f"Given the statements above, is there anything that {p_name} should remember as they plan for"
    plan_prompt += f" *{role.scratch.curr_time.strftime('%A %B %d')}*? "
    plan_prompt += "If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement)\n\n"
    plan_prompt += f"Write the response from {p_name}'s perspective."
    plan_note = LLM().ask(plan_prompt)

    thought_prompt = statements + "\n"
    thought_prompt += (
        f"Given the statements above, how might we summarize {p_name}'s feelings about their days up to now?\n\n"
    )
    thought_prompt += f"Write the response from {p_name}'s perspective."
    thought_note = LLM().ask(thought_prompt)

    currently_prompt = (
        f"{p_name}'s status from {(role.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}:\n"
    )
    currently_prompt += f"{role.scratch.currently}\n\n"
    currently_prompt += f"{p_name}'s thoughts at the end of {(role.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}:\n"
    currently_prompt += (plan_note + thought_note).replace("\n", "") + "\n\n"
    currently_prompt += f"It is now {role.scratch.curr_time.strftime('%A %B %d')}. Given the above, write {p_name}'s status for {role.scratch.curr_time.strftime('%A %B %d')} that reflects {p_name}'s thoughts at the end of {(role.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}. Write this in third-person talking about {p_name}."
    currently_prompt += "If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement).\n\n"
    currently_prompt += "Follow this format below:\nStatus: <new status>"
    new_currently = LLM().ask(currently_prompt)

    role.scratch.currently = new_currently

    daily_req_prompt = role.scratch.get_str_iss() + "\n"
    daily_req_prompt += f"Today is {role.scratch.curr_time.strftime('%A %B %d')}. Here is {role.scratch.name}'s plan today in broad-strokes (with the time of the day. e.g., have a lunch at 12:00 pm, watch TV from 7 to 8 pm).\n\n"
    daily_req_prompt += "Follow this format (the list should have 4~6 items but no more):\n"
    daily_req_prompt += "1. wake up and complete the morning routine at <time>, 2. ..."

    new_daily_req = LLM().ask(daily_req_prompt)
    new_daily_req = new_daily_req.replace("\n", " ")
    role.scratch.daily_plan_req = new_daily_req
