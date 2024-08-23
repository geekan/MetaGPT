INITIALIZE_OPERATOR_PROMPT = """
您正在处理一个名为{dataset_name}的数据集。该数据集{dataset_description}。

输入特征包括:
{input_features}

输出特征为:
{output_features}

请根据以上信息,优化用途为{operator_name}的prompt以便更好地处理这个数据集:

{initial_prompt}

您的任务是:
1. 分析数据集的特点和结构
2. 考虑输入和输出特征之间的关系
3. 调整initial_prompt以更好地利用数据集信息
4. 提供一个经过优化的prompt版本

请提供您优化后的prompt,并简要解释您所做的更改及其原因。
"""

# TODO 这里也需要自适应的完成针对不同数据集的GRAPH OPTIMIZE PROMPT

GRAPH_OPTIMIZE_PROMPT = """You are building a Graph and corresponding Prompt to jointly solve mathematical problems.
Referring to the given combination of graph and prompt, which forms a basic example of a mathematical solution approach, please reconstruct and optimize the Prompt and Graph. You can add, modify, or delete nodes and parameters in the graph, as well as modify, delete, or add new Prompts.
Put your modification (only make one point of change, i.e., one sentence), and the modified Prompt and Graph in XML tags in your reply. They will be used as new Prompt and Graph for calculation and iteration. Please ensure they are complete and correct, otherwise it may lead to runtime failures.
Only modify the parts in Prompt and Graph within /async def __call__(self, problem: str):/, otherwise it will cause parsing failure.
Reply format (must be strictly followed) (do not include any other formats except for the given XML format):

<modification>You should fill in the details of your modifications here, to facilitate future review.</modification>
<graph>graph</graph>
<prompt>prompt</prompt>

When optimizing, you can refer to critical thinking, and can incorporate methods such as Review, Revise, Ensemble, selfAsk, etc. Don't be limited to the previous format.You can consider Python's built-in loops (like for, while, and list comprehensions) or conditional statements (such as if-elif-else and ternary operators), or even machine learning methods ranging from basic supervised learning techniques (e.g., linear regression, decision trees) to more advanced approaches like neural networks and clustering algorithms. However, you must ensure that each call to the Graph internally involves at most 10 interactions, i.e., the complexity of the graph does not exceed 15."""
