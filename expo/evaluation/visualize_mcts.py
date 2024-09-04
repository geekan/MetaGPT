import textwrap

from expo.MCTS import Node

NODE_TEMPLATE = """\
[Node {id}]
Plans: 
{plans}
Simulated: {simulated}
Score: {score}, Visits: {num_visits}

"""


def get_role_plans(role):
    plans = role.planner.plan.tasks
    instruct_plans = [f"{i+1}. {task.instruction}" for i, task in enumerate(plans)]
    return instruct_plans


def get_tree_text(node: Node):
    role_dict = {}
    code_set = set()

    def load_role(node):
        if node.id not in role_dict:
            role_dict[node.id] = node.load_role()
        return role_dict[node.id]

    def visualize_node(node: Node, previous_plans=None):
        role = load_role(node)
        node_id = node.id
        plans = role.planner.plan.tasks
        instruct_plans = [f"{i+1}. {task.instruction}" for i, task in enumerate(plans)]
        if previous_plans is not None:
            instruct_plans = [plan for plan, prev_plan in zip(instruct_plans, previous_plans) if plan != prev_plan]
        instruct_plans_text = "\n".join(instruct_plans)
        simulated = role.state_saved
        score = f"avg score: {node.avg_value()}, simulated score: {node.raw_reward}"
        num_visits = node.visited
        return NODE_TEMPLATE.format(
            id=node_id, plans=instruct_plans_text, simulated=simulated, score=score, num_visits=num_visits
        )

    def visualize_tree(node, depth=0, previous_plans=None):
        text = ""
        if node is not None:
            text += visualize_node(node, previous_plans)
            role = load_role(node)
            code_set.update({task.instruction for task in role.planner.plan.tasks})
            previous_plans = get_role_plans(role)
            for child in node.children:
                text += textwrap.indent(visualize_tree(child, depth + 1, previous_plans), "\t")
        return text

    num_simulations = node.visited
    text = f"Number of simulations: {num_simulations}\n"
    text += visualize_tree(node)
    return text, len(code_set)
