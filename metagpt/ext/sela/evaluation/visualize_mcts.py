import textwrap

import matplotlib.pyplot as plt
import networkx as nx

from metagpt.ext.sela.search.tree_search import Node

NODE_TEMPLATE = """\
[Node {id}]
Plans: 
{plans}
Simulated: {simulated}
Score: {score}, Visits: {num_visits}

"""

NODE_SIZE = 12000
NODE_FONT_SIZE = 18


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

    def visualize_tree_text(node, depth=0, previous_plans=None):
        text = ""
        if node is not None:
            text += visualize_node(node, previous_plans)
            role = load_role(node)
            code_set.update({task.instruction for task in role.planner.plan.tasks})
            previous_plans = get_role_plans(role)
            for child in node.children:
                text += textwrap.indent(visualize_tree_text(child, depth + 1, previous_plans), "\t")
        return text

    num_simulations = node.visited
    text = f"Number of simulations: {num_simulations}\n"
    text += visualize_tree_text(node)
    return text, len(code_set)


def get_node_color(node):
    if node["visits"] == 0:
        return "#D3D3D3"
    else:
        # The higher the avg_value, the more intense the color
        # avg_value is between 0 and 1
        avg_value = node["avg_value"]
        # Convert avg_value to a color ranging from red (low) to green (high)
        red = int(255 * (1 - avg_value))
        green = int(255 * avg_value)
        return f"#{red:02X}{green:02X}00"


def visualize_tree(graph, show_instructions=False, save_path=""):
    # Use a hierarchical layout for tree-like visualization
    pos = nx.spring_layout(graph, k=0.9, iterations=50)

    plt.figure(figsize=(30, 20))  # Further increase figure size for better visibility

    # Calculate node levels
    root = "0"
    levels = nx.single_source_shortest_path_length(graph, root)
    max_level = max(levels.values())

    # Adjust y-coordinates based on levels and x-coordinates to prevent overlap
    nodes_by_level = {}
    for node, level in levels.items():
        if level not in nodes_by_level:
            nodes_by_level[level] = []
        nodes_by_level[level].append(node)

    for level, nodes in nodes_by_level.items():
        y = 1 - level / max_level
        x_step = 1.0 / (len(nodes) + 1)
        for i, node in enumerate(sorted(nodes)):
            pos[node] = ((i + 1) * x_step, y)

    # Draw edges
    nx.draw_networkx_edges(graph, pos, edge_color="gray", arrows=True, arrowsize=40, width=3)

    # Draw nodes
    node_colors = [get_node_color(graph.nodes[node]) for node in graph.nodes]
    nx.draw_networkx_nodes(graph, pos, node_size=NODE_SIZE, node_color=node_colors)

    # Add labels to nodes
    labels = nx.get_node_attributes(graph, "label")
    nx.draw_networkx_labels(graph, pos, labels, font_size=NODE_FONT_SIZE)

    if show_instructions:
        # Add instructions to the right side of nodes
        instructions = nx.get_node_attributes(graph, "instruction")
        for node, (x, y) in pos.items():
            wrapped_text = textwrap.fill(instructions[node], width=30)  # Adjust width as needed
            plt.text(x + 0.05, y, wrapped_text, fontsize=15, ha="left", va="center")

    plt.title("MCTS Tree Visualization", fontsize=40)
    plt.axis("off")  # Turn off axis
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()


def build_tree_recursive(graph, parent_id, node, node_order, start_task_id=2):
    """
    Recursively builds the entire tree starting from the root node.
    Adds nodes and edges to the NetworkX graph.
    """
    role = node.load_role()
    depth = node.get_depth()
    if depth == 0:
        instruction = "\n\n".join([role.planner.plan.tasks[i].instruction for i in range(start_task_id)])
    else:
        instruction = role.planner.plan.tasks[depth + start_task_id - 1].instruction
    print(instruction)
    # Add the current node with attributes to the graph
    dev_score = node.raw_reward.get("dev_score", 0) * 100
    avg_score = node.avg_value() * 100
    order = node_order.index(node.id) if node.id in node_order else ""
    graph.add_node(
        parent_id,
        label=f"{node.id}\nAvg: {avg_score:.1f}\nScore: {dev_score:.1f}\nVisits: {node.visited}\nOrder: {order}",
        avg_value=node.avg_value(),
        dev_score=dev_score,
        visits=node.visited,
        instruction=instruction,
    )
    # Stopping condition: if the node has no children, return
    if not node.children:
        return

    # Recursively create all child nodes
    for i, child in enumerate(node.children):
        child_id = f"{parent_id}-{i}"
        graph.add_edge(parent_id, child_id)
        build_tree_recursive(graph, child_id, child, node_order)
