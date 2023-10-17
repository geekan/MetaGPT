class ChainOfThoughtBase(object):

    def __init__(self, prompt, aask, task) -> None:
        self.prompt = prompt
        self.aask = aask
        self.task = task

    async def solve(self, max_num_rounds = 5):
        
        for _ in max_num_rounds:
            for prompt_template, step_output in zip(self.task.prompts, self.task.task_output_keys):
                message = self.prompter.generate_initial_prompt(prompt_template, **self.task.task_args_pool)
                self.task.task_args_pool[step_output] = await self.aask(message)
                solution = self.task.task_args_pool[step_output]
            solution_found, messages = self.checker(solution)

            if solution_found:
                print(messages)
                return True, solution
            
        print("Failed to solve within {} rounds of conversations.".format(max_num_rounds))
        return False, None

class ChainOfThoughtForEngineer(ChainOfThoughtBase):

    def __init__(self, config) -> None:
        super().__init__()
        self.prompter = None
        pass

    