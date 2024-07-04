# 第一段代码是MedPrompt，一种利用利用LLM产生多种答案，然后进行洗牌投票来选出最优决策的方法
# 我需要你首先理解这个方法，然后将这个方法与我的代码结合起来
# 我的代码如下，我们会接收到多个答案，我需要你将这个答案利用MedPrompt的方法进行处理。
# 在我的代码中，产生llm answer是用 await ActionNode.from_pydantic(ScEnsembleOp).fill(context=prompt, llm=self.llm) 实现的。

class ScEnsemble(Ensemble):

    def __init__(self, name:str ="Ensembler", llm: LLM = LLM()):
        super().__init__(name, llm)

    async def __call__(self, solutions:List, problem_description):
        solution_text = ""
        for index, solution in enumerate(solutions):
            solution_text += f"Solution{index}: {str(solution)}" + "\n"

        prompt = ENSEMBLE_PROMPT.format(solutions=solution_text, problem_description=problem_description)
        node = await ActionNode.from_pydantic(ScEnsembleOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()
        return response

class Medprompt(QASystem):
    def __init__(
        self,
        agents: list,
        num_reasoning_steps: int,
        debate_prompts: dict,
        verbose: bool = False,
        name: Optional[str] = None,
        mock: bool = False,  # Unused
        agent_prompts: Optional[dict] = None,  # Unused
    ):
        super().__init__(verbose=verbose)

        assert len(agents) == 1
        self._num_reasoning_steps = num_reasoning_steps
        self._agent = agents[0]
        self._agent_names = [type(agent).__name__ for agent in agents]
        self.prompts = debate_prompts

    """
    This is an implementation of the Medprompt system take
    from https://arxiv.org/abs/2311.16452

    The system is comprised of a single agent prompted to provide multiple
    answers and explainations via temperature sampling and question shuffling.
    The final answer is determined by taking the most frequent answer provided
    by the agent during the aggregation.

    IMPORTANT: The current implementation only contains the first three steps
    of the Medprompt setup. Therefore additional improvements can be made
    by including the kNN and Ensemble with choice shuffling as well.
    """

    # Setup debate metrics
    def metrics(
        self, info: Dict[str, Any], format_solution_fn: Callable, solution: str
    ) -> Dict[str, Any]:
        return construct_agent_metrics(
            info=info,
            format_solution_fn=format_solution_fn,
            solution=solution,
            verbose=self._verbose,
            agents=["Agent_0"],
            agent_names=self._agent_names,
            num_rounds=self._num_reasoning_steps,
        )

    @staticmethod
    def shuffle_answers(question: str) -> Tuple[str, Any]:
        """
        Takes in a multiple choice question string and shuffles only the answer texts,
        keeping the answer labels (A, B, C, etc.) intact.
        Also returns a mapping of shuffled choices to original choices.
        """
        # Find the start of the answer section (e.g., '\nA:')
        answer_section_start = re.search(r"\n[A-Z]:", question).start()  # type: ignore

        # Split the question from the answers
        main_question = question[:answer_section_start]
        answers = question[answer_section_start + 1 :].split("\n")

        # Filter out answers that are not in the correct format
        # answers = [answer for answer in answers if ": " == answer[1:3]]

        # Extract answer texts
        answer_texts = [answer.split(": ", 1)[1] for answer in answers]

        # assert len(answer_texts) > 0

        # Shuffle the answer texts and create a mapping to original answers
        shuffled_texts = answer_texts.copy()
        random.shuffle(shuffled_texts)
        answer_mapping = {
            chr(65 + i): answers[answer_texts.index(text)][0]
            for i, text in enumerate(shuffled_texts)
        }

        # Reassemble the shuffled answers with original labels
        shuffled_answers = [
            f"{chr(65 + i)}: {text}" for i, text in enumerate(shuffled_texts)
        ]

        # Reassemble the question
        shuffled_question = main_question + "\n" + "\n".join(shuffled_answers)
        return shuffled_question, answer_mapping

    def answer(
        self,
        question: str,
    ) -> Tuple[str, Any]:

        agent_answers: Any = {"Agent_0": {}}
        agent_info: Any = {"Agent_0": {}}
        agent_responses: Any = {"Agent_0": {}}
        if self._verbose:
            print("#######################")
            print("REASONING STEP")
            print("#######################")

        message_history: List[Dict[str, str]] = []

        for i in range(self._num_reasoning_steps):

            try:
                # TODO: Provide the options to the system as well. This would
                # make it much easier to shuffle the answers. Furthermore, remove
                # all questions without options in load_datasets.py.
                shuffled_question, answer_mapping = self.shuffle_answers(question)
            except Exception as e:
                shuffled_question = question
                answer_mapping = {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"}
                print("question: ", question)
                print("Shuffling failed, using original question: ", e)

            answer, info = self._agent.answer(
                question=shuffled_question,
                system_message=self.prompts["system"],
            )

            # Dummy data to check the suffler.
            # answer = "A"
            # info = {"prompt_tokens": 1234, "response_tokens": 1234,
            #       "response": "I don't know, A.",
            #       "cost": 0.0, "num_messages_removed": 0.0,
            #       "answer_duration": 1.0, "engine": "Diesel"}

            # Map the answer back to the original answer
            if answer in answer_mapping:
                answer = answer_mapping[answer]

            message_history.append(
                {"agent_name": f"Reasoning_{i}", "content": info["response"]}
            )
            agent_answers["Agent_0"][f"Reasoning_{i}"] = answer
            agent_responses["Agent_0"][f"Reasoning_{i}"] = info["response"]
            agent_info["Agent_0"][f"Reasoning_{i}"] = info

        final_answers = [
            agent_answers["Agent_0"][f"Reasoning_{i}"]
            for i in range(self._num_reasoning_steps)
        ]
        answer, _ = most_frequent(final_answers)

        return answer, {
            "response": agent_responses,
            "agent_answers": agent_answers,
            "agent_info": agent_info,
        }