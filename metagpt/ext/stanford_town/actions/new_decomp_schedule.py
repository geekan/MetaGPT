#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : new_decomp_schedule

import datetime

from metagpt.ext.stanford_town.actions.st_action import STAction
from metagpt.logs import logger


class NewDecompSchedule(STAction):
    name: str = "NewDecompSchedule"

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        resp = False
        try:
            llm_resp = self._func_cleanup(llm_resp, prompt)
            dur_sum = 0
            for act, dur in llm_resp:
                dur_sum += dur
                if isinstance(act, str):
                    return False
                if isinstance(dur, int):
                    return False
            x = prompt.split("\n")[0].split("originally planned schedule from")[-1].strip()[:-1]
            x = [datetime.datetime.strptime(i.strip(), "%H:%M %p") for i in x.split(" to ")]
            delta_min = int((x[1] - x[0]).total_seconds() / 60)

            if int(dur_sum) != int(delta_min):
                return False
        except Exception:
            pass
        return resp

    def _func_cleanup(self, llm_resp: str, prompt: str) -> list:
        new_schedule = prompt + " " + llm_resp.strip()
        new_schedule = new_schedule.split("The revised schedule:")[-1].strip()
        new_schedule = new_schedule.split("\n")

        ret_temp = []
        for i in new_schedule:
            ret_temp += [i.split(" -- ")]

        ret = []
        for time_str, action in ret_temp:
            start_time = time_str.split(" ~ ")[0].strip()
            end_time = time_str.split(" ~ ")[1].strip()
            delta = datetime.datetime.strptime(end_time, "%H:%M") - datetime.datetime.strptime(start_time, "%H:%M")
            delta_min = int(delta.total_seconds() / 60)
            if delta_min < 0:
                delta_min = 0
            ret += [[action, delta_min]]

        return ret

    def _func_fail_default_resp(self, main_act_dur: int, truncated_act_dur: int) -> int:
        dur_sum = 0
        for act, dur in main_act_dur:
            dur_sum += dur

        ret = truncated_act_dur[:]
        ret += main_act_dur[len(ret) - 1 :]

        # If there are access, we need to trim...
        ret_dur_sum = 0
        count = 0
        over = None
        for act, dur in ret:
            ret_dur_sum += dur
            if ret_dur_sum == dur_sum:
                break
            if ret_dur_sum > dur_sum:
                over = ret_dur_sum - dur_sum
                break
            count += 1

        if over:
            ret = ret[: count + 1]
            ret[-1][1] -= over

        return ret

    async def run(
        self,
        role: "STRole",
        main_act_dur: int,
        truncated_act_dur: int,
        start_time_hour: datetime,
        end_time_hour: datetime,
        inserted_act: str,
        inserted_act_dur: int,
        *args,
        **kwargs,
    ):
        def create_prompt_input(
            role: "STRole",
            main_act_dur: int,
            truncated_act_dur: int,
            start_time_hour: datetime,
            end_time_hour: datetime,
            inserted_act: str,
            inserted_act_dur: int,
        ):
            persona_name = role.name
            start_hour_str = start_time_hour.strftime("%H:%M %p")
            end_hour_str = end_time_hour.strftime("%H:%M %p")

            original_plan = ""
            for_time = start_time_hour
            for i in main_act_dur:
                original_plan += (
                    f'{for_time.strftime("%H:%M")} ~ '
                    f'{(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- ' + i[0]
                )
                original_plan += "\n"
                for_time += datetime.timedelta(minutes=int(i[1]))

            new_plan_init = ""
            for_time = start_time_hour
            for count, i in enumerate(truncated_act_dur):
                new_plan_init += (
                    f'{for_time.strftime("%H:%M")} ~ '
                    f'{(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- ' + i[0]
                )
                new_plan_init += "\n"
                if count < len(truncated_act_dur) - 1:
                    for_time += datetime.timedelta(minutes=int(i[1]))

            new_plan_init += (for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M") + " ~"

            prompt_input = [
                persona_name,
                start_hour_str,
                end_hour_str,
                original_plan,
                persona_name,
                inserted_act,
                inserted_act_dur,
                persona_name,
                start_hour_str,
                end_hour_str,
                end_hour_str,
                new_plan_init,
            ]
            return prompt_input

        prompt_input = create_prompt_input(
            role, main_act_dur, truncated_act_dur, start_time_hour, end_time_hour, inserted_act, inserted_act_dur
        )
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input, "new_decomp_schedule_v1.txt")
        self.fail_default_resp = self._func_fail_default_resp(main_act_dur, truncated_act_dur)
        output = await self._run_gpt35_max_tokens(prompt, max_tokens=1000)
        logger.info(f"Role: {role.name} Action: {self.cls_name} output: {output}")
        return output
