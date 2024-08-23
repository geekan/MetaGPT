class Gsm8kGraph(Graph):
    def __init__(self, name: str, llm: LLM, criteria: str, vote_count: int = 5) -> None:
        super().__init__(name, llm)
        self.criteria = criteria
        self.generate = Generate(llm=llm)
        self.rephrase = Rephrase(llm=llm)
        self.fuensemble = FuEnsemble(llm=llm)
        self.mdensemble = MdEnsemble(llm=llm, vote_count=vote_count)
        self.review = Review(llm=llm, criteria=criteria)
        self.revise = Revise(llm=llm)
        self.format = Format(llm=llm)

    async def __call__(self, problem: str):
        rephrased_problem = await self.rephrase.math_rephrase(problem)
        solution = await self.generate.math_generate(rephrased_problem)
        formatted_solution = await self.format.math_answer_format(solution["solution"])
        return formatted_solution

    async def baseline(self, problem: str):
        solution = await self.generate(problem)
        formatted_solution = await self.format.math_answer_format(solution["solution"])
        return formatted_solution

    async def simple_ensemble(self, problem: str, ensemble_count: int = 3):
        rephrased_problem = await self.rephrase.math_rephrase(problem)
        solution_list = []
        answer_list = []

        for _ in range(ensemble_count):
            solution = await self.generate.math_generate(rephrased_problem)
            solution = solution.get("solution")
            answer = await self.format.math_answer_format(solution)
            solution_list.append(solution)
            answer_list.append(answer)

        if len(set(answer.get("solution") for answer in answer_list)) == 1:
            formatted_solution = answer_list[0]
        else:
            # TODO 我个人感觉针对数学这种情景，使用self consistency 的ensemble方法可能会更好
            solution = await self.mdensemble("math", solution_list, problem)
            formatted_solution = await self.format.math_answer_format(solution["final_solution"])

        return formatted_solution

    async def single_solve(self, problem: str, max_loop: int = 3):
        rephrased_problem = await self.rephrase.math_rephrase(problem)
        solution = await self.generate.math_generate(rephrased_problem)
        for _ in range(max_loop):
            review_feedback = await self.review(rephrased_problem, solution["solution"])
            if review_feedback["review_result"]:
                break
            solution = await self.revise(rephrased_problem, solution["solution"], review_feedback["feedback"])
            solution = solution.get("revised_solution")
        formatted_solution = await self.format.math_answer_format(solution)
        return formatted_solution

    async def cot_ensemble(self, problem: str, ensemble_count: int = 1):
        solution_list = []
        for _ in range(ensemble_count):
            core = await self.rephrase.math_core(problem)
            extract = await self.rephrase.math_extract(problem)
            formatted_problem = (
                f"### Problem\n{problem}\n### Problem-Solving Info\n{extract}\n### Core Question\n{core}\n"
            )
            solution = await self.generate.math_generate(formatted_problem)  # 等待 generate 方法完成
            solution0 = solution.get("solution")
            solution_list.append(solution0)
        solution = await self.fuensemble(solution_list, problem)
        solution0 = solution["solution"]
        formatted_solution = await self.format.math_answer_format(solution)
        return formatted_solution

    async def cot(self, problem: str):
        core = await self.rephrase.math_core(problem)
        extract = await self.rephrase.math_extract(problem)
        formatted_problem = f"### Problem\n{problem}\n### Problem-Solving Info\n{extract}\n### Core Question\n{core}\n"
        solution = await self.generate.math_generate(formatted_problem)  # 等待 generate 方法完成
        solution.get("solution")
        formatted_solution = await self.format.math_answer_format(solution)

        return formatted_solution
