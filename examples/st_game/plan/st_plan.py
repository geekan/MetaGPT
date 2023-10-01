#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : st' planning execution

import random
from typing import Union, Tuple
from datetime import datetime
import math

from ..maze import Maze
from ..plan.converse import agent_conversation
from ..roles.st_role import STRole
from ..actions.decide_to_talk import DecideToTalk
from ..actions.summarize_conv import SummarizeConv
from ..actions.new_decomp_schedule import NewDecompSchedule


def plan(role: STRole, maze: Maze, roles: list[STRole], new_day: bool, retrieved: dict):

    focused_event = False
    if retrieved.keys():
        focused_event = _choose_retrieved(role, retrieved)

    # Step 2: Once we choose an event, we need to determine whether the
    #         persona will take any actions for the perceived event. There are
    #         three possible modes of reaction returned by _should_react.
    #         a) "chat with {target_persona.name}"
    #         b) "react"
    #         c) False
    if focused_event:
        reaction_mode = _should_react(role, focused_event, roles)
        if reaction_mode:
            # If we do want to chat, then we generate conversation
            if reaction_mode[:9] == "chat with":
                _chat_react(maze, role, focused_event, reaction_mode, roles)
            elif reaction_mode[:4] == "wait":
                _wait_react(role, reaction_mode)


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
        if (":" not in curr_event.subject
                and curr_event.subject != role_name):
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


def _should_react(role: "STRole", retrieved: dict, roles: dict):
    """
    Determines what form of reaction the persona should exihibit given the
    retrieved values.
    INPUT
      role: Current <STRole> instance whose action we are determining.
      retrieved: A dictionary of <ConceptNode> that were retrieved from the
                 the role's associative memory. This dictionary takes the
                 following form:
                 dictionary[event.description] =
                   {["curr_event"] = <ConceptNode>,
                    ["events"] = [<ConceptNode>, ...],
                    ["thoughts"] = [<ConceptNode>, ...] }
      roles: A dictionary that contains all role names as keys, and the
                <STRole> instance as values.
    """

    def lets_talk(init_role: STRole, target_role: STRole, retrieved: dict):
        scratch = init_role._rc.scratch
        target_scratch = target_role._rc.scratch
        if (not target_scratch.act_address
                or not target_scratch.act_description
                or not scratch.act_address
                or not scratch.act_description):
            return False

        if ("sleeping" in target_scratch.act_description
                or "sleeping" in scratch.act_description):
            return False

        if scratch.curr_time.hour == 23:
            return False

        if "<waiting>" in target_scratch.act_address:
            return False

        if (target_scratch.chatting_with
                or scratch.chatting_with):
            return False

        if (target_role.name in scratch.chatting_with_buffer):
            if scratch.chatting_with_buffer[target_role.name] > 0:
                return False

        if DecideToTalk().run(init_role, target_role, retrieved):
            return True

        return False

    def lets_react(init_role: STRole, target_role: STRole, retrieved: dict):
        scratch = init_role._rc.scratch
        target_scratch = target_role._rc.scratch
        if (not target_scratch.act_address
                or not target_scratch.act_description
                or not scratch.act_address
                or not scratch.act_description):
            return False

        if ("sleeping" in target_scratch.act_description
                or "sleeping" in scratch.act_description):
            return False

        # return False
        if scratch.curr_time.hour == 23:
            return False

        if "waiting" in target_scratch.act_description:
            return False
        if scratch.planned_path == []:
            return False

        if (scratch.act_address
                != target_scratch.act_address):
            return False

        react_mode = DecideToTalk().run(init_role,
                                        target_role,
                                        retrieved)

        if react_mode == "1":
            wait_until = ((target_scratch.act_start_time
                           + datetime.timedelta(minutes=target_scratch.act_duration - 1))
                          .strftime("%B %d, %Y, %H:%M:%S"))
            return f"wait: {wait_until}"
        elif react_mode == "2":
            return False
            return "do other things"
        else:
            return False  # "keep"

    # If the persona is chatting right now, default to no reaction
    scratch = role._rc.scratch
    if scratch.chatting_with:
        return False
    if "<waiting>" in scratch.act_address:
        return False

    # Recall that retrieved takes the following form:
    # dictionary {["curr_event"] = <ConceptNode>}
    curr_event = retrieved["curr_event"]

    if ":" not in curr_event.subject:
        # this is a persona event.
        if lets_talk(role, roles[curr_event.subject], retrieved):
            return f"chat with {curr_event.subject}"
        react_mode = lets_react(role, roles[curr_event.subject],
                                retrieved)
        return react_mode
    return False


def _chat_react(maze: Maze, role: STRole, reaction_mode: str, roles: list[STRole]):
    # There are two personas -- the persona who is initiating the conversation
    # and the persona who is the target. We get the persona instances here.
    init_role = role
    target_role = roles[reaction_mode[9:].strip()]
    curr_personas = [init_role, target_role]

    # Actually creating the conversation here.
    convo, duration_min = generate_convo(maze, init_role, target_role)  # 2222
    convo_summary = generate_convo_summary(init_role, convo)
    inserted_act = convo_summary
    inserted_act_dur = duration_min

    act_start_time = target_role._rc.scratch.act_start_time

    curr_time = target_role._rc.scratch.curr_time
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

        _create_react(p, inserted_act, inserted_act_dur,
                      act_address, act_event, chatting_with, convo, chatting_with_buffer, chatting_end_time,
                      act_pronunciatio, act_obj_description, act_obj_pronunciatio,
                      act_obj_event, act_start_time)


def _create_react(role: STRole, inserted_act: str, inserted_act_dur: int,
                  act_address: str, act_event: Tuple, chatting_with: str, chat: list, chatting_with_buffer: dict,
                  chatting_end_time: datetime,
                  act_pronunciatio: str, act_obj_description: str, act_obj_pronunciatio: str,
                  act_obj_event: Tuple, act_start_time=None):
    p = role
    scratch = role._rc.scratch

    min_sum = 0
    for i in range(scratch.get_f_daily_schedule_hourly_org_index()):
        min_sum += scratch.f_daily_schedule_hourly_org[i][1]
    start_hour = int(min_sum / 60)

    if (scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1] >= 120):
        end_hour = start_hour + \
                   scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1] / 60

    elif (scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1] +
          scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index() + 1][1]):
        end_hour = start_hour + (
                    (scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1] +
                     scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index() + 1][
                         1]) / 60)

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

    ret = generate_new_decomp_schedule(p, inserted_act, inserted_act_dur,
                                       start_hour, end_hour)
    scratch.f_daily_schedule[start_index:end_index] = ret
    scratch.add_new_action(act_address,
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
                           act_start_time)


def _wait_react(role: STRole, reaction_mode: str):
    scratch = role._rc.scratch

    inserted_act = f'waiting to start {scratch.act_description.split("(")[-1][:-1]}'
    end_time = datetime.datetime.strptime(reaction_mode[6:].strip(), "%B %d, %Y, %H:%M:%S")
    inserted_act_dur = (end_time.minute + end_time.hour * 60) - (
                scratch.curr_time.minute + scratch.curr_time.hour * 60) + 1

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

    _create_react(role, inserted_act, inserted_act_dur,
                  act_address, act_event, chatting_with, chat, chatting_with_buffer, chatting_end_time,
                  act_pronunciatio, act_obj_description, act_obj_pronunciatio, act_obj_event)


def generate_convo(maze: Maze, init_role: STRole, target_role: STRole) -> Union[list, int]:
    curr_loc = maze.access_tile(init_role._rc.scratch.curr_tile)
    convo = agent_conversation(maze, init_role, target_role)
    all_utt = ""

    for row in convo:
        speaker = row[0]
        utt = row[1]
        all_utt += f"{speaker}: {utt}\n"

    convo_length = math.ceil(int(len(all_utt) / 8) / 30)

    return convo, convo_length


def generate_convo_summary(role: STRole, conv: list) -> str:
    conv_summary = SummarizeConv().run(conv)
    return conv_summary


def generate_new_decomp_schedule(role: STRole, inserted_act: str, inserted_act_dur: int,
                                 start_hour: int, end_hour: int):
    # Step 1: Setting up the core variables for the function.
    # <p> is the persona whose schedule we are editing right now.
    p = role
    scratch = role._rc.scratch
    # <today_min_pass> indicates the number of minutes that have passed today.
    today_min_pass = (int(scratch.curr_time.hour) * 60
                      + int(scratch.curr_time.minute) + 1)

    # Step 2: We need to create <main_act_dur> and <truncated_act_dur>.
    main_act_dur = []
    truncated_act_dur = []
    dur_sum = 0  # duration sum
    count = 0  # enumerate count
    truncated_fin = False

    print("DEBUG::: ", scratch.name)
    for act, dur in scratch.f_daily_schedule:
        if (dur_sum >= start_hour * 60) and (dur_sum < end_hour * 60):
            main_act_dur += [[act, dur]]
            if dur_sum <= today_min_pass:
                truncated_act_dur += [[act, dur]]
            elif dur_sum > today_min_pass and not truncated_fin:
                # We need to insert that last act, duration list like this one:
                # e.g., ['wakes up and completes her morning routine (wakes up...)', 2]
                truncated_act_dur += [[scratch.f_daily_schedule[count][0],
                                       dur_sum - today_min_pass]]
                truncated_act_dur[-1][-1] -= (
                            dur_sum - today_min_pass)  # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass + 1)
                print("DEBUG::: ", truncated_act_dur)

                # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass)
                truncated_fin = True
        dur_sum += dur
        count += 1

    persona_name = role.name
    main_act_dur = main_act_dur

    x = truncated_act_dur[-1][0].split("(")[0].strip() + " (on the way to " + truncated_act_dur[-1][0].split("(")[-1][
                                                                              :-1] + ")"
    truncated_act_dur[-1][0] = x

    if "(" in truncated_act_dur[-1][0]:
        inserted_act = truncated_act_dur[-1][0].split("(")[0].strip() + " (" + inserted_act + ")"

    # To do inserted_act_dur+1 below is an important decision but I'm not sure
    # if I understand the full extent of its implications. Might want to
    # revisit.
    truncated_act_dur += [[inserted_act, inserted_act_dur]]
    start_time_hour = (datetime.datetime(2022, 10, 31, 0, 0)
                       + datetime.timedelta(hours=start_hour))
    end_time_hour = (datetime.datetime(2022, 10, 31, 0, 0)
                     + datetime.timedelta(hours=end_hour))

    return NewDecompSchedule().run(role,
                                   main_act_dur,
                                   truncated_act_dur,
                                   start_time_hour,
                                   end_time_hour,
                                   inserted_act,
                                   inserted_act_dur)
