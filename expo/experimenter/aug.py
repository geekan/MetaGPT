from experimenter import Experimenter

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
        exp_pool = InstructionGenerator.load_analysis_pool(exp_pool_path)
        if self.args.aug_mode == "single":
            exps = InstructionGenerator._random_sample(exp_pool, self.args.num_experiments)
            exps = [exp["Analysis"] for exp in exps]
        elif self.args.aug_mode == "set":
            exp_set = InstructionGenerator.sample_instruction_set(exp_pool)
            exp_set_text = "\n".join([f"{exp['task_id']}: {exp['Analysis']}" for exp in exp_set])
            exps = [exp_set_text] * self.args.num_experiments
        else:
            raise ValueError(f"Invalid mode: {self.args.aug_mode}")

        results = []
        for i in range(self.args.num_experiments):
            di = ResearchAssistant(node_id=str(i), use_reflection=self.args.reflection)
            di.role_dir = f"{di.role_dir}_{self.args.task}"
            requirement = user_requirement + EXPS_PROMPT.format(experience=exps[i])
            print(requirement)
            score_dict = await self.run_di(di, requirement)
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
        scores = [result["score_dict"]["test_score"] for result in results]
        avg_score = sum(scores) / len(scores)
        best_score = max(scores) if not self.args.low_is_better else min(scores)
        best_score_idx = scores.index(best_score)
        results.insert(0, {"avg_score": avg_score, "best_score": best_score, "best_score_idx": best_score_idx})
        self.save_result(results)
