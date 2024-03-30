#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Scratch类实现（角色信息类）

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, Field, field_serializer, field_validator

from metagpt.utils.common import read_json_file, write_json_file


class Scratch(BaseModel):
    # 类别1:人物超参
    vision_r: int = 4
    att_bandwidth: int = 3
    retention: int = 5

    # 类别2:世界信息
    curr_time: Optional[datetime] = Field(default=None)
    curr_tile: Optional[list[int]] = Field(default=None)
    daily_plan_req: Optional[str] = Field(default=None)

    # 类别3:人物角色的核心身份
    name: Optional[str] = Field(default=None)
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    age: Optional[int] = Field(default=None)
    innate: Optional[str] = Field(default=None)  # L0 permanent core traits.
    learned: Optional[str] = Field(default=None)  # L1 stable traits.
    currently: Optional[str] = Field(default=None)  # L2 external implementation.
    lifestyle: Optional[str] = Field(default=None)
    living_area: Optional[str] = Field(default=None)

    # 类别4:旧反思变量
    concept_forget: int = 100
    daily_reflection_time: int = 60 * 3
    daily_reflection_size: int = 5
    overlap_reflect_th: int = 2
    kw_strg_event_reflect_th: int = 4
    kw_strg_thought_reflect_th: int = 4

    # 类别5:新反思变量
    recency_w: int = 1
    relevance_w: int = 1
    importance_w: int = 1
    recency_decay: float = 0.99
    importance_trigger_max: int = 150
    importance_trigger_curr: int = 150
    importance_ele_n: int = 0
    thought_count: int = 5

    # 类别6:个人计划
    daily_req: list[str] = Field(default=[])
    f_daily_schedule: list[list[Union[int, str]]] = Field(default=[])
    f_daily_schedule_hourly_org: list[list[Union[int, str]]] = Field(default=[])

    # 类别7:当前动作
    act_address: Optional[str] = Field(default=None)
    act_start_time: Optional[datetime] = Field(default=None)
    act_duration: Optional[int] = Field(default=None)
    act_description: Optional[str] = Field(default=None)
    act_pronunciatio: Optional[str] = Field(default=None)
    act_event: list[Optional[str]] = [None, None, None]

    act_obj_description: Optional[str] = Field(default=None)
    act_obj_pronunciatio: Optional[str] = Field(default=None)
    act_obj_event: list[Optional[str]] = [None, None, None]

    chatting_with: Optional[str] = Field(default=None)
    chat: Optional[str] = Field(default=None)
    chatting_with_buffer: dict = dict()
    chatting_end_time: Optional[datetime] = Field(default=None)

    act_path_set: bool = False
    planned_path: list[list[int]] = Field(default=[])

    @field_validator("curr_time", "act_start_time", "chatting_end_time", mode="before")
    @classmethod
    def check_time_filed(cls, time_filed):
        val = datetime.strptime(time_filed, "%B %d, %Y, %H:%M:%S") if time_filed else None
        return val

    @field_serializer("curr_time", "act_start_time", "chatting_end_time")
    def transform_time_field(self, time_filed: Optional[datetime]) -> str:
        if time_filed:
            time_filed = time_filed.strftime("%B %d, %Y, %H:%M:%S")
        return time_filed

    @classmethod
    def init_scratch_from_path(cls, f_saved: Path):
        scratch_load = read_json_file(f_saved)
        scratch = Scratch(**scratch_load)
        return scratch

    def save(self, out_json: Path):
        """
        Save persona's scratch.

        INPUT:
          out_json: The file where we wil be saving our persona's state.
        OUTPUT:
          None
        """
        scratch = self.model_dump()
        write_json_file(out_json, scratch, encoding="utf-8")

    def get_f_daily_schedule_index(self, advance=0):
        """
        We get the current index of self.f_daily_schedule.

        Recall that self.f_daily_schedule stores the decomposed action sequences
        up until now, and the hourly sequences of the future action for the rest
        of today. Given that self.f_daily_schedule is a list of list where the
        inner list is composed of [task, duration], we continue to add up the
        duration until we reach "if elapsed > today_min_elapsed" condition. The
        index where we stop is the index we will return.

        INPUT
          advance: Integer value of the number minutes we want to look into the
                   future. This allows us to get the index of a future timeframe.
        OUTPUT
          an integer value for the current index of f_daily_schedule.
        """
        # We first calculate teh number of minutes elapsed today.
        today_min_elapsed = 0
        today_min_elapsed += self.curr_time.hour * 60
        today_min_elapsed += self.curr_time.minute
        today_min_elapsed += advance

        x = 0
        for task, duration in self.f_daily_schedule:
            x += duration
        x = 0
        for task, duration in self.f_daily_schedule_hourly_org:
            x += duration

        # We then calculate the current index based on that.
        curr_index = 0
        elapsed = 0
        for task, duration in self.f_daily_schedule:
            elapsed += duration
            if elapsed > today_min_elapsed:
                return curr_index
            curr_index += 1

        return curr_index

    def get_f_daily_schedule_hourly_org_index(self, advance=0):
        """
        We get the current index of self.f_daily_schedule_hourly_org.
        It is otherwise the same as get_f_daily_schedule_index.

        INPUT
          advance: Integer value of the number minutes we want to look into the
                   future. This allows us to get the index of a future timeframe.
        OUTPUT
          an integer value for the current index of f_daily_schedule.
        """
        # We first calculate teh number of minutes elapsed today.
        today_min_elapsed = 0
        today_min_elapsed += self.curr_time.hour * 60
        today_min_elapsed += self.curr_time.minute
        today_min_elapsed += advance
        # We then calculate the current index based on that.
        curr_index = 0
        elapsed = 0
        for task, duration in self.f_daily_schedule_hourly_org:
            elapsed += duration
            if elapsed > today_min_elapsed:
                return curr_index
            curr_index += 1
        return curr_index

    def get_str_iss(self):
        """
        ISS stands for "identity stable set." This describes the commonset summary
        of this persona -- basically, the bare minimum description of the persona
        that gets used in almost all prompts that need to call on the persona.

        INPUT
          None
        OUTPUT
          the identity stable set summary of the persona in a string form.
        EXAMPLE STR OUTPUT
          "Name: Dolores Heitmiller
           Age: 28
           Innate traits: hard-edged, independent, loyal
           Learned traits: Dolores is a painter who wants live quietly and paint
             while enjoying her everyday life.
           Currently: Dolores is preparing for her first solo show. She mostly
             works from home.
           Lifestyle: Dolores goes to bed around 11pm, sleeps for 7 hours, eats
             dinner around 6pm.
           Daily plan requirement: Dolores is planning to stay at home all day and
             never go out."
        """
        commonset = ""
        commonset += f"Name: {self.name}\n"
        commonset += f"Age: {self.age}\n"
        commonset += f"Innate traits: {self.innate}\n"
        commonset += f"Learned traits: {self.learned}\n"
        commonset += f"Currently: {self.currently}\n"
        commonset += f"Lifestyle: {self.lifestyle}\n"
        commonset += f"Daily plan requirement: {self.daily_plan_req}\n"
        commonset += f"Current Date: {self.curr_time.strftime('%A %B %d') if self.curr_time else ''}\n"
        return commonset

    def get_str_name(self):
        return self.name

    def get_str_firstname(self):
        return self.first_name

    def get_str_lastname(self):
        return self.last_name

    def get_str_age(self):
        return str(self.age)

    def get_str_innate(self):
        return self.innate

    def get_str_learned(self):
        return self.learned

    def get_str_currently(self):
        return self.currently

    def get_str_lifestyle(self):
        return self.lifestyle

    def get_str_daily_plan_req(self):
        return self.daily_plan_req

    def get_str_curr_date_str(self):
        return self.curr_time.strftime("%A %B %d")

    def get_curr_event(self):
        if not self.act_address:
            return self.name, None, None
        else:
            return self.act_event

    def get_curr_event_and_desc(self):
        if not self.act_address:
            return self.name, None, None, None
        else:
            return self.act_event[0], self.act_event[1], self.act_event[2], self.act_description

    def get_curr_obj_event_and_desc(self):
        if not self.act_address:
            return "", None, None, None
        else:
            return self.act_address, self.act_obj_event[1], self.act_obj_event[2], self.act_obj_description

    def add_new_action(
        self,
        action_address,
        action_duration,
        action_description,
        action_pronunciatio,
        action_event,
        chatting_with,
        chat,
        chatting_with_buffer,
        chatting_end_time,
        act_obj_description,
        act_obj_pronunciatio,
        act_obj_event,
        act_start_time=None,
    ):
        self.act_address = action_address
        self.act_duration = action_duration
        self.act_description = action_description
        self.act_pronunciatio = action_pronunciatio
        self.act_event = action_event

        self.chatting_with = chatting_with
        self.chat = chat
        if chatting_with_buffer:
            self.chatting_with_buffer.update(chatting_with_buffer)
        self.chatting_end_time = chatting_end_time

        self.act_obj_description = act_obj_description
        self.act_obj_pronunciatio = act_obj_pronunciatio
        self.act_obj_event = act_obj_event

        self.act_start_time = self.curr_time

        self.act_path_set = False

    def act_time_str(self):
        """
        Returns a string output of the current time.

        INPUT
          None
        OUTPUT
          A string output of the current time.
        EXAMPLE STR OUTPUT
          "14:05 P.M."
        """
        return self.act_start_time.strftime("%H:%M %p")

    def act_check_finished(self):
        """
        Checks whether the self.Action instance has finished.

        INPUT
          curr_datetime: Current time. If current time is later than the action's
                         start time + its duration, then the action has finished.
        OUTPUT
          Boolean [True]: Action has finished.
          Boolean [False]: Action has not finished and is still ongoing.
        """
        if not self.act_address:
            return True

        if self.chatting_with:
            end_time = self.chatting_end_time
        else:
            x = self.act_start_time
            if x.second != 0:
                x = x.replace(second=0)
                x = x + timedelta(minutes=1)
            end_time = x + timedelta(minutes=self.act_duration)

        if end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S"):
            return True
        return False

    def act_summarize(self):
        """
        Summarize the current action as a dictionary.

        INPUT
          None
        OUTPUT
          ret: A human readable summary of the action.
        """
        exp = dict()
        exp["persona"] = self.name
        exp["address"] = self.act_address
        exp["start_datetime"] = self.act_start_time
        exp["duration"] = self.act_duration
        exp["description"] = self.act_description
        exp["pronunciatio"] = self.act_pronunciatio
        return exp

    def act_summary_str(self):
        """
        Returns a string summary of the current action. Meant to be
        human-readable.

        INPUT
          None
        OUTPUT
          ret: A human readable summary of the action.
        """
        start_datetime_str = self.act_start_time.strftime("%A %B %d -- %H:%M %p")
        ret = f"[{start_datetime_str}]\n"
        ret += f"Activity: {self.name} is {self.act_description}\n"
        ret += f"Address: {self.act_address}\n"
        ret += f"Duration in minutes (e.g., x min): {str(self.act_duration)} min\n"
        return ret

    def get_daily_schedule(self, daily_schedule: list[list[str]]):
        ret = ""
        curr_min_sum = 0
        for row in daily_schedule:
            curr_min_sum += row[1]
            hour = int(curr_min_sum / 60)
            minute = curr_min_sum % 60
            ret += f"{hour:02}:{minute:02} || {row[0]}\n"
        return ret

    def get_str_daily_schedule_summary(self):
        return self.get_daily_schedule(self.f_daily_schedule)

    def get_str_daily_schedule_hourly_org_summary(self):
        return self.get_daily_schedule(self.f_daily_schedule_hourly_org)
