import json
from metagpt.utils.common import CodeParser

class TreeOfThoughtBase(object):

    def __init__(self, prompt, aask, task) -> None:
        self.prompt = prompt
        self.aask = aask
        self.task = task

    async def solve(self, max_num_rounds = 5):
        prompt_template = self.task.prompts[0]
        message = self.prompter.generate_initial_prompt(prompt_template, **self.task.task_args_pool)

        for _ in range(max_num_rounds):
            reply = await self.aask(message)
            self._incr_state_visit_count()

            self.conversation_history += "\nA: {}".format(reply)

            success, solution = self.parser.parse_code(block="", text=reply)
            if not success:
                print("Failed to extract solution from the reply, will retry")
                continue # retry
            self.state_manager.update_state(solution)

            rollback_steps = self._get_rollback_steps()
            solution_found, solution, curr_state_is_valid, messages = self.prompter.generate_prompt(self.conversation_history, rollback_steps) # FIXME
            if solution_found:
                print(messages)
                return True, solution
            
            if not curr_state_is_valid:
                self.state_manager.rollback(rollback_steps) # backtracking

        print("Failed to solve within {} rounds of conversations.".format(max_num_rounds))
        return False, None

    def _incr_state_visit_count(self):
        if self.state_manager.get_current_state() is None:
            return
        curr_state_key = json.dumps(self.state_manager.get_current_state().tolist())
        if not (curr_state_key in self.state_manager_visit_count_map):
            self.state_manager_visit_count_map[curr_state_key] = 0
        self.state_manager_visit_count_map[curr_state_key] += 1
        print("\nVISIT COUNT for {}: {}\n".format(curr_state_key, self.state_manager_visit_count_map[curr_state_key]))
    
    def _get_parent_state_visit_count(self):
        parent_state = self.state_manager.get_state(rollback_steps = 1)
        if parent_state is None:
            return 0
        parent_state_key = json.dumps(parent_state.tolist())
        if not (parent_state_key in self.state_manager_visit_count_map):
            return 0
        else:
            return self.state_manager_visit_count_map[parent_state_key]

class TreeOfThoughtForEngineer(TreeOfThoughtBase):

    def __init__(self, config) -> None:
        super().__init__()
        self.state_manager = None
        self.parser = CodeParser
        self.prompter = None

    pass