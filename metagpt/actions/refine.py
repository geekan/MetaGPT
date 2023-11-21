from metagpt.actions import Action


# 增量开发动作的基类
class Refine(Action):
    def __init__(self, name="Refine", context=None, llm=None):
        super().__init__(name, context, llm)

    def run(self, *args, **kwargs):
        raise NotImplementedError
