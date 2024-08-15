import matplotlib.pyplot as plt
import networkx as nx


def convert_tasks_to_graph(tasks):
    G = nx.DiGraph()  # Create a directed graph

    for task in tasks:
        task_id = task.get("task_id", None) or task["id"]
        G.add_node(task_id, label=task.get("name", f"Task {task_id}"))

        # Add edges for each dependency
        for dep_id in task.get("dependent_task_ids", []):
            G.add_edge(dep_id, task_id)

    return G


def plot_graph(G):
    pos = nx.spring_layout(G)
    labels = nx.get_node_attributes(G, "label")
    nx.draw(
        G,
        pos,
        labels=labels,
        with_labels=True,
        node_size=3000,
        node_color="skyblue",
        font_size=10,
        font_weight="bold",
        arrows=True,
    )
    plt.show()
