from metagpt.actions import Action, ActionOutput
from metagpt.logs import logger



class TalkAction(Action):
    def __init__(self, options, name: str = '', talk='', history_summary='', context=None, llm=None, **kwargs):
        context = context or {}
        context["talk"] = talk
        context["history_summery"] = history_summary
        super(TalkAction, self).__init__(options=options, name=name, context=context, llm=llm)
        self._talk = talk
        self._history_summary = history_summary
        self._rsp = None

    @property
    def prompt(self):
        prompt = f"{self._history_summary}\n\n"
        if self._history_summary != "":
            prompt += "According to the historical conversation above, "
        language = self.options.get("language", "Chinese")
        prompt += f"Answer in {language}:\n {self._talk}"
        return prompt

    async def run(self, *args, **kwargs) -> ActionOutput:
        prompt = self.prompt
        logger.info(prompt)
        rsp = await self.llm.aask(msg=prompt, system_msgs=[])
        logger.info(rsp)
        self._rsp = ActionOutput(content=rsp)
        return self._rsp

