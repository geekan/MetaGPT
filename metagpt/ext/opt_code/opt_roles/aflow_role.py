from metagpt.ext.opt_code.opt_roles.experimenter import Experimenter
from metagpt.ext.opt_code.memory.aflow_memory import AFlowNode
from metagpt.actions.action_node import ActionNode
from pydantic import BaseModel, Field
from metagpt.logs import logger
from metagpt.provider.llm_provider_registry import create_llm_instance

import os
import json
from typing import Tuple
import re
import string
from collections import Counter
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

AFLOW_PROMPT = """
Here is a graph and the corresponding prompt (prompt only related to the custom method) that performed excellently in a previous iteration (maximum score is 1). You must make further optimizations and improvements based on this graph. The modified graph must differ from the provided example, and the specific differences should be noted within the <modification>xxx</modification> section.\n
<sample>
    <experience>{experience}</experience>
    <modification>(such as:add a review step/delete an operator/modify a prompt)</modification>
    <score>{score}</score>
    <graph>{graph}</graph>
    <prompt>{prompt}</prompt>(only prompt_custom)
    <operator_description>{operator_description}</operator_description>
</sample>
Below are the logs of some results with the aforementioned Graph that performed well but encountered errors, which can be used as references for optimization:
{log}

First, provide optimization ideas. **Only one detail point can be modified at a time**, and no more than 5 lines of code may be changed per modification—extensive modifications are strictly prohibited to maintain project focus!
When introducing new functionalities in the graph, please make sure to import the necessary libraries or modules yourself, except for operator, prompt_custom, create_llm_instance, and CostManage, which have already been automatically imported.
**Under no circumstances should Graph output None for any field.**
Use custom methods to restrict your output format, rather than using code (outside of the code, the system will extract answers based on certain rules and score them).
It is very important to format the Graph output answers, you can refer to the standard answer format in the log.
"""

EXAMPLE = """
\nHere's an example of using the `custom` method in graph:
```
# You can write your own prompt in <prompt>prompt_custom</prompt> and then use it in the Custom method in the graph
response = await self.custom(input=problem, instruction=prompt_custom.XXX_PROMPT)
# You can also concatenate previously generated string results in the input to provide more comprehensive contextual information.
# response = await self.custom(input=problem+f"xxx:{xxx}, xxx:{xxx}", instruction=prompt_custom.XXX_PROMPT)
# The output from the Custom method can be placed anywhere you need it, as shown in the example below
solution = await self.generate(problem=f"question:{problem}, xxx:{response['response']}")
```
Note: In custom, the input and instruction are directly concatenated(instruction+input), and placeholders are not supported. Please ensure to add comments and handle the concatenation externally.\n

**Introducing multiple operators at appropriate points can enhance performance. If you find that some provided operators are not yet used in the graph, try incorporating them.**
"""

OPTIMIZE_PROMPT = """
You are building a Graph and corresponding Prompt to jointly solve {type} problems. 
Referring to the given graph and prompt, which forms a basic example of a {type} solution approach, 
please reconstruct and optimize them. You can add, modify, or delete nodes, parameters, or prompts. Include your 
single modification in XML tags in your reply. Ensure they are complete and correct to avoid runtime failures. When 
optimizing, you can incorporate critical thinking methods like review, revise, ensemble (generating multiple answers through different/similar prompts, then voting/integrating/checking the majority to obtain a final answer), selfAsk, etc. Consider 
Python's loops (for, while, list comprehensions), conditional statements (if-elif-else, ternary operators), 
or machine learning techniques (e.g., linear regression, decision trees, neural networks, clustering). The graph 
complexity should not exceed 10. Use logical and control flow (IF-ELSE, loops) for a more enhanced graphical 
representation.Ensure that all the prompts required by the current graph from prompt_custom are included.Exclude any other prompts.
Output the modified graph and all the necessary Prompts in prompt_custom (if needed).
The prompt you need to generate is only the one used in `prompt_custom.XXX` within Custom. Other methods already have built-in prompts and are prohibited from being generated. Only generate those needed for use in `prompt_custom`; please remove any unused prompts in prompt_custom.
the generated prompt must not contain any placeholders.
Considering information loss, complex graphs may yield better results, but insufficient information transmission can omit the solution. It's crucial to include necessary context during the process."""

WORKFLOW_TEMPLATE = """
from typing import Literal
import metagpt.ext.opt_code.data.template.operator as operator
import metagpt.ext.opt_code.optimized.{dataset}.roles.{name}.prompt as prompt_custom
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.utils.cost_manager import CostManager

DatasetType = Literal["HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP"]

{graph}
""" # TODO fix the path

class GraphOptimize(BaseModel):
    modification: str = Field(default="", description="modification")
    graph: str = Field(default="", description="graph")
    prompt: str = Field(default="", description="prompt")

DATASET2PATH = {
    "GSM8K": "metagpt/ext/opt_code/data/gsm8k_train.jsonl",
    "HotpotQA": "metagpt/ext/opt_code/data/hotpotqa_train.jsonl",
}

class AflowRole(Experimenter):
    async def initialize(self, node, kwargs: dict, root_path):
        self.llm_config = kwargs["llm_config"]
        self.exec_llm_config = kwargs["exec_llm_config"]
        self.dataset = kwargs["dataset"]
        self.data_path = DATASET2PATH[self.dataset]
        return await super().initialize(node, kwargs, root_path)

    async def _generate(self, node: AFlowNode, context):
        graph_input = AFLOW_PROMPT.format(
            experience=context["experience"],
            score=node.reward,
            graph=node.code,
            prompt=node.prompt,
            operator_description=context["operator_description"],
            type=context["data_type"],
            log=context["log_data"],
        )

        graph_system = OPTIMIZE_PROMPT.format(type=context["data_type"])

        prompt = graph_input + EXAMPLE + graph_system

        response = await ActionNode.from_pydantic(GraphOptimize).fill(
            context=prompt, mode="xml_fill", llm=self.llm
        )
        response =  response.instruct_content.model_dump()

        node.code = response["graph"]
        node.prompt = response["prompt"]
        node.modification_info = response["modification"]

    def _save_files(self, path, response, new_name):
        os.makedirs(path, exist_ok=True)

        graph = WORKFLOW_TEMPLATE.format(graph=response["graph"], name=new_name, dataset=self.dataset)

        with open(os.path.join(path, "graph.py"), "w", encoding="utf-8") as file:
            file.write(graph)

        with open(os.path.join(path, "prompt.py"), "w", encoding="utf-8") as file:
            file.write(response["prompt"])

        with open(os.path.join(path, "__init__.py"), "w", encoding="utf-8") as file:
            file.write("")
    
    async def _execute(self, node: AFlowNode):
        # 这里先保存
        name = "node_" + node.id
            
        file_path = os.path.join(self.root_path, name)
        self._save_files(file_path, {"graph": node.code, "prompt": node.prompt}, name)

        workflow_path = file_path.replace("\\", ".").replace("/", ".")
        graph_module_name = f"{workflow_path}.graph"
        
        result = {
            "score": 0,
            "log_data": []
        }

        try:
            graph_module = __import__(graph_module_name, fromlist=[""])
            graph_class = getattr(graph_module, "Workflow")
            graph = graph_class(name=f"{node.id}_optimized", llm_config=self.exec_llm_config, dataset=self.dataset)
            data = self.load_dataset()
            avg_score, log_data = await self._eval(graph, data)

            result["score"] = avg_score
            result["log_data"] = log_data        
        except ImportError as e:
            logger.info(f"Error loading graph for node {node.id}: {e}")

        return result

    def load_dataset(self):
        data = []
        with open(self.data_path, "r") as f:
            for line in f:
                data.append(json.loads(line))
        return data
    
    async def _eval(self, executor, data):
        # 需要实现不同数据集
        def normalize_answer(s: str) -> str:
            def remove_articles(text):
                return re.sub(r"\b(a|an|the)\b", " ", text)

            def white_space_fix(text):
                return " ".join(text.split())

            def remove_punc(text):
                exclude = set(string.punctuation)
                return "".join(ch for ch in text if ch not in exclude)

            def lower(text):
                return text.lower()

            return white_space_fix(remove_articles(remove_punc(lower(s))))
        
        def calculate_score(ground_truth: str, prediction: str) -> Tuple[float, str]:
            prediction_tokens = normalize_answer(prediction).split()
            ground_truth_tokens = normalize_answer(ground_truth).split()
            common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
            num_same = sum(common.values())
            if num_same == 0:
                return 0, prediction
            precision = 1.0 * num_same / len(prediction_tokens)
            recall = 1.0 * num_same / len(ground_truth_tokens)
            f1 = (2 * precision * recall) / (precision + recall)
            return f1, prediction

        @retry(stop=stop_after_attempt(5), wait=wait_fixed(1), retry=retry_if_exception_type(Exception), reraise=True)
        async def _exec(executor, input):
            return await executor(input)
        
        avg_score = 0
        log_data = []
        
        for d in data:
            query = d["question"]
            answer = d["answer"]
            paragraphs = [item[1] for item in d["context"] if isinstance(item[1], list)]
            context_str = "\n".join(" ".join(paragraph) for paragraph in paragraphs)
            inputs = f"Context: {context_str}\n\nQuestion: {query}\n\nAnswer:"
            try:
                output, cost = await _exec(executor, inputs)
                score, extracted_output = calculate_score(answer, output)
            except Exception as e:
                print("Error {}".format(e))
                score = 0
                extracted_output = "Error"

            avg_score += score
            if score < 0.3:
                log_data.append({"question": query, "wrong_answer": answer, "correct_answer": extracted_output, "score": score})
            
        return avg_score / len(data), log_data
    
    async def run(self, node: AFlowNode, context=None, instruction=None):
        if context is None:
            # node is root node
            return await self._execute(node)
        else:
            await self._generate(node, context)
            return await self._execute(node)
        

