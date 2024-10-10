from expo.experimenter.experimenter import Experimenter
from expo.insights.instruction_generator import InstructionGenerator
from expo.research_assistant import ResearchAssistant
from expo.utils import get_exp_pool_path

EXPS_PROMPT = """
When doing the tasks, you can refer to the insights below:
{experience}

"""


class AugExperimenter(Experimenter):
    result_path: str = "results/aug"

    async def run_experiment(self):
        # state = create_initial_state(self.args.task, start_task_id=1, data_config=self.data_config, low_is_better=self.args.low_is_better, name="")
        user_requirement = self.state["requirement"]
        exp_pool_path = get_exp_pool_path(self.args.task, self.data_config, pool_name="ds_analysis_pool")
        exp_pool = InstructionGenerator.load_analysis_pool(
            exp_pool_path, use_fixed_insights=self.args.use_fixed_insights
        )
        if self.args.aug_mode == "single":
            exps = InstructionGenerator._random_sample(exp_pool, self.args.num_experiments)
            exps = [exp["Analysis"] for exp in exps]
        elif self.args.aug_mode == "set":
            exps = []
            for i in range(self.args.num_experiments):
                exp_set = InstructionGenerator.sample_instruction_set(exp_pool)
                exp_set_text = "\n".join([f"{exp['task_id']}: {exp['Analysis']}" for exp in exp_set])
                exps.append(exp_set_text)
        else:
            raise ValueError(f"Invalid mode: {self.args.aug_mode}")

        results = []
        for i in range(self.args.num_experiments):
            di = ResearchAssistant(node_id=str(i), use_reflection=self.args.reflection)
            di.role_dir = f"{di.role_dir}_{self.args.task}"
            requirement = user_requirement + EXPS_PROMPT.format(experience=exps[i])
            print(requirement)
            score_dict = await self.run_di(di, requirement, run_idx=i)
            results.append(
                {
                    "idx": i,
                    "score_dict": score_dict,
                    "aug_mode": self.args.aug_mode,
                    "insights": exps[i],
                    "user_requirement": requirement,
                    "args": vars(self.args),
                }
            )
        results = self.summarize_results(results)
        self.save_result(results)
