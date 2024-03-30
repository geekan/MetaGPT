#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : task_decomp

import datetime

from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


class TaskDecomp(STAction):
    name: str = "TaskDecomp"

    def _func_cleanup(self, llm_resp: str, prompt: str) -> list:
        # TODO SOMETHING HERE sometimes fails... See screenshot
        temp = [i.strip() for i in llm_resp.split("\n")]
        _cr = []
        cr = []
        for count, i in enumerate(temp):
            if count != 0:
                _cr += [" ".join([j.strip() for j in i.split(" ")][3:])]
            else:
                _cr += [i]
        for count, i in enumerate(_cr):
            k = [j.strip() for j in i.split("(duration in minutes:")]
            task = k[0]
            if task[-1] == ".":
                task = task[:-1]
            duration = int(k[1].split(",")[0].strip())
            cr += [[task, duration]]

        total_expected_min = int(prompt.split("(total duration in minutes")[-1].split("):")[0].strip())

        # TODO -- now, you need to make sure that this is the same as the sum of
        #         the current action sequence.
        curr_min_slot = [
            ["dummy", -1],
        ]  # (task_name, task_index)
        for count, i in enumerate(cr):
            i_task = i[0]
            i_duration = i[1]

            i_duration -= i_duration % 5
            if i_duration > 0:
                for j in range(i_duration):
                    curr_min_slot += [(i_task, count)]
        curr_min_slot = curr_min_slot[1:]

        if len(curr_min_slot) > total_expected_min:
            last_task = curr_min_slot[60]
            for i in range(1, 6):
                curr_min_slot[-1 * i] = last_task
        elif len(curr_min_slot) < total_expected_min:
            last_task = curr_min_slot[-1]
            for i in range(total_expected_min - len(curr_min_slot)):
                curr_min_slot += [last_task]

        cr_ret = [
            ["dummy", -1],
        ]
        for task, task_index in curr_min_slot:
            if task != cr_ret[-1][0]:
                cr_ret += [[task, 1]]
            else:
                cr_ret[-1][1] += 1
        cr = cr_ret[1:]

        return cr

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        # TODO -- this sometimes generates error
        try:
            self._func_cleanup(llm_resp, prompt)
        except Exception:
            return False
        return True

    def _func_fail_default_resp(self) -> int:
        fs = [["asleep", 0]]
        return fs

    async def run(self, role: "STRole", task_desc: int, truncated_act_dur: int, *args, **kwargs):
        def create_prompt_input(role, task, duration):
            """
            Today is Saturday June 25. From 00:00 ~ 06:00am, Maeve is
            planning on sleeping, 06:00 ~ 07:00am, Maeve is
            planning on waking up and doing her morning routine,
            and from 07:00am ~08:00am, Maeve is planning on having breakfast.
            """

            curr_f_org_index = role.scratch.get_f_daily_schedule_hourly_org_index()
            all_indices = []
            # if curr_f_org_index > 0:
            #   all_indices += [curr_f_org_index-1]
            all_indices += [curr_f_org_index]
            if curr_f_org_index + 1 <= len(role.scratch.f_daily_schedule_hourly_org):
                all_indices += [curr_f_org_index + 1]
            if curr_f_org_index + 2 <= len(role.scratch.f_daily_schedule_hourly_org):
                all_indices += [curr_f_org_index + 2]

            curr_time_range = ""

            logger.debug("DEBUG")
            logger.debug(role.scratch.f_daily_schedule_hourly_org)
            logger.debug(all_indices)

            summ_str = f'Today is {role.scratch.curr_time.strftime("%B %d, %Y")}. '
            summ_str += "From "
            for index in all_indices:
                logger.debug(f"index {index}")
                if index < len(role.scratch.f_daily_schedule_hourly_org):
                    start_min = 0
                    for i in range(index):
                        start_min += role.scratch.f_daily_schedule_hourly_org[i][1]
                        end_min = start_min + role.scratch.f_daily_schedule_hourly_org[index][1]
                        start_time = datetime.datetime.strptime("00:00:00", "%H:%M:%S") + datetime.timedelta(
                            minutes=start_min
                        )
                        end_time = datetime.datetime.strptime("00:00:00", "%H:%M:%S") + datetime.timedelta(
                            minutes=end_min
                        )
                        start_time_str = start_time.strftime("%H:%M%p")
                        end_time_str = end_time.strftime("%H:%M%p")
                        summ_str += (
                            f"{start_time_str} ~ {end_time_str}, {role.name} is planning "
                            f"on {role.scratch.f_daily_schedule_hourly_org[index][0]}, "
                        )
                        if curr_f_org_index + 1 == index:
                            curr_time_range = f"{start_time_str} ~ {end_time_str}"
            summ_str = summ_str[:-2] + "."

            prompt_input = []
            prompt_input += [role.scratch.get_str_iss()]
            prompt_input += [summ_str]
            # prompt_input += [role.scratch.get_str_curr_date_str()]
            prompt_input += [role.scratch.get_str_firstname()]
            prompt_input += [role.scratch.get_str_firstname()]
            prompt_input += [task]
            prompt_input += [curr_time_range]
            prompt_input += [duration]
            prompt_input += [role.scratch.get_str_firstname()]
            return prompt_input

        prompt_input = create_prompt_input(role, task_desc, truncated_act_dur)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, "task_decomp_v3.txt")
        self.fail_default_resp = self._func_fail_default_resp()
        output = await self._run_gpt35_max_tokens(prompt, max_tokens=1000)
        logger.info(f"Role: {role.name} {self.cls_name} output: {output}")

        fin_output = []
        time_sum = 0
        for i_task, i_duration in output:
            time_sum += i_duration
            # HM?????????
            # if time_sum < duration:
            if time_sum <= truncated_act_dur:
                fin_output += [[i_task, i_duration]]
            else:
                break
        ftime_sum = 0
        for fi_task, fi_duration in fin_output:
            ftime_sum += fi_duration

        fin_output[-1][1] += truncated_act_dur - ftime_sum
        output = fin_output

        task_decomp = output
        ret = []
        for decomp_task, duration in task_decomp:
            ret += [[f"{task_desc} ({decomp_task})", duration]]
        output = ret
        logger.info(f"Role: {role.name} Action: {self.cls_name} output: {output}")
        return output
