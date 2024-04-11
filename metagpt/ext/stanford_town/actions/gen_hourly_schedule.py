#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : gen_hourly_schedule

import random
import string

from metagpt.logs import logger

from .st_action import STAction


def get_random_alphanumeric(i=6, j=6):
    """
    Returns a random alpha numeric strength that has the length of somewhere
    between i and j.

    INPUT:
        i: min_range for the length
        j: max_range for the length
    OUTPUT:
        an alpha numeric str with the length of somewhere between i and j.
    """
    k = random.randint(i, j)
    x = "".join(random.choices(string.ascii_letters + string.digits, k=k))
    return x


class GenHourlySchedule(STAction):
    name: str = "GenHourlySchedule"

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try:
            self._func_cleanup(llm_resp, prompt="")
        except Exception:
            return False
        return True

    def _func_cleanup(self, llm_resp: str, prompt: str) -> list:
        cr = llm_resp.strip()
        if cr[-1] == ".":
            cr = cr[:-1]
        # to only use the first line of output
        cr = cr.split("\n")[0]
        return cr

    def _func_fail_default_resp(self) -> int:
        fs = "asleep"
        return fs

    async def _generate_schedule_for_given_hour(
        self, role: "STRole", curr_hour_str, p_f_ds_hourly_org, hour_str, intermission2=None
    ):
        def create_prompt_input(persona, curr_hour_str, p_f_ds_hourly_org, hour_str, intermission2=None):
            schedule_format = ""
            for i in hour_str:
                schedule_format += f"[{persona.scratch.get_str_curr_date_str()} -- {i}]"
                schedule_format += " Activity: [Fill in]\n"
            schedule_format = schedule_format[:-1]

            intermission_str = "Here the originally intended hourly breakdown of"
            intermission_str += f" {persona.scratch.get_str_firstname()}'s schedule today: "
            for count, i in enumerate(persona.scratch.daily_req):
                intermission_str += f"{str(count + 1)}) {i}, "
            intermission_str = intermission_str[:-2]

            prior_schedule = ""
            if p_f_ds_hourly_org:
                prior_schedule = "\n"
                for count, i in enumerate(p_f_ds_hourly_org):
                    prior_schedule += f"[(ID:{get_random_alphanumeric()})"
                    prior_schedule += f" {persona.scratch.get_str_curr_date_str()} --"
                    prior_schedule += f" {hour_str[count]}] Activity:"
                    prior_schedule += f" {persona.scratch.get_str_firstname()}"
                    prior_schedule += f" is {i}\n"

            prompt_ending = f"[(ID:{get_random_alphanumeric()})"
            prompt_ending += f" {persona.scratch.get_str_curr_date_str()}"
            prompt_ending += f" -- {curr_hour_str}] Activity:"
            prompt_ending += f" {persona.scratch.get_str_firstname()} is"

            if intermission2:
                intermission2 = f"\n{intermission2}"

            prompt_input = []
            prompt_input += [schedule_format]
            prompt_input += [persona.scratch.get_str_iss()]

            prompt_input += [prior_schedule + "\n"]
            prompt_input += [intermission_str]
            if intermission2:
                prompt_input += [intermission2]
            else:
                prompt_input += [""]
                prompt_input += [prompt_ending]

            return prompt_input

        prompt_template = "generate_hourly_schedule_v2.txt"
        prompt_input = create_prompt_input(role, curr_hour_str, p_f_ds_hourly_org, hour_str, intermission2)
        prompt_input_str = "\n".join(prompt_input)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, prompt_template)
        self.fail_default_resp = self._func_fail_default_resp()
        output = await self._run_gpt35_max_tokens(prompt, max_tokens=50)
        logger.info(
            f"Role: {role.name} _generate_schedule_for_given_hour prompt_input: {prompt_input_str}, "
            f"output: {output}"
        )
        return output

    async def run(self, role: "STRole", wake_up_hour: int):
        hour_str = [
            "00:00 AM",
            "01:00 AM",
            "02:00 AM",
            "03:00 AM",
            "04:00 AM",
            "05:00 AM",
            "06:00 AM",
            "07:00 AM",
            "08:00 AM",
            "09:00 AM",
            "10:00 AM",
            "11:00 AM",
            "12:00 PM",
            "01:00 PM",
            "02:00 PM",
            "03:00 PM",
            "04:00 PM",
            "05:00 PM",
            "06:00 PM",
            "07:00 PM",
            "08:00 PM",
            "09:00 PM",
            "10:00 PM",
            "11:00 PM",
        ]
        n_m1_activity = []
        diversity_repeat_count = 1  # TODO mg 1->3
        for i in range(diversity_repeat_count):
            logger.info(f"diversity_repeat_count idx: {i}")
            n_m1_activity_set = set(n_m1_activity)
            if len(n_m1_activity_set) < 5:
                n_m1_activity = []
                for count, curr_hour_str in enumerate(hour_str):
                    if wake_up_hour > 0:
                        n_m1_activity += ["sleeping"]
                        wake_up_hour -= 1
                    else:
                        logger.info(f"_generate_schedule_for_given_hour idx: {count}, n_m1_activity: {n_m1_activity}")
                        n_m1_activity += [
                            await self._generate_schedule_for_given_hour(role, curr_hour_str, n_m1_activity, hour_str)
                        ]

        # Step 1. Compressing the hourly schedule to the following format:
        # The integer indicates the number of hours. They should add up to 24.
        # [['sleeping', 6], ['waking up and starting her morning routine', 1],
        # ['eating breakfast', 1], ['getting ready for the day', 1],
        # ['working on her painting', 2], ['taking a break', 1],
        # ['having lunch', 1], ['working on her painting', 3],
        # ['taking a break', 2], ['working on her painting', 2],
        # ['relaxing and watching TV', 1], ['going to bed', 1], ['sleeping', 2]]
        _n_m1_hourly_compressed = []
        prev = None
        prev_count = 0
        for i in n_m1_activity:
            if i != prev:
                prev_count = 1
                _n_m1_hourly_compressed += [[i, prev_count]]
                prev = i
            elif _n_m1_hourly_compressed:
                _n_m1_hourly_compressed[-1][1] += 1

        # Step 2. Expand to min scale (from hour scale)
        # [['sleeping', 360], ['waking up and starting her morning routine', 60],
        # ['eating breakfast', 60],..
        n_m1_hourly_compressed = []
        for task, duration in _n_m1_hourly_compressed:
            n_m1_hourly_compressed += [[task, duration * 60]]
        logger.info(f"Role: {role.name} Action: {self.cls_name} output: {n_m1_hourly_compressed}")
        return n_m1_hourly_compressed
