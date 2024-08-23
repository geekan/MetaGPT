class HotpotQAGraph(Graph):
    def __init__(self, name: str, llm: LLM, criteria: str, HOTPOTQA_PATH: str) -> None:
        super().__init__(name, llm)
        self.generate = Generate(llm=llm)
        self.format = Format(llm=llm)
        self.review = Review(llm=llm, criteria=criteria)
        self.revise = Revise(llm=llm)
        self.hotpotqa_path = HOTPOTQA_PATH

    async def __call__(self, id: str, max_loop: int = 1):
        dp = get_hotpotqa(self.hotpotqa_path)[id]
        paragraphs = [item[1] for item in dp["context"] if isinstance(item[1], list)]
        context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)

        answer_result = await self.generate.context_solution_generate(dp["question"], context_str)
        answer_result = answer_result.get("solution")

        for _ in range(max_loop):
            review_result = await self.review(dp["question"], answer_result)
            if review_result["review_result"]:
                break
            answer_result = await self.revise(dp["question"], answer_result, review_result["feedback"])
            answer_result = answer_result.get("revised_solution")

        answer_formated = await self.format(dp["question"], answer_result)

        sample_dict = dict(task_id=id, answer=answer_formated.get("solution"))
        return sample_dict
