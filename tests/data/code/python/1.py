"""
===============
Degree Analysis
===============

This example shows several ways to visualize the distribution of the degree of
nodes with two common techniques: a *degree-rank plot* and a
*degree histogram*.

In this example, a random Graph is generated with 100 nodes. The degree of
each node is determined, and a figure is generated showing three things:
1. The subgraph of connected components
2. The degree-rank plot for the Graph, and
3. The degree histogram
"""
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

G = nx.gnp_random_graph(100, 0.02, seed=10374196)

degree_sequence = sorted((d for n, d in G.degree()), reverse=True)
dmax = max(degree_sequence)

fig = plt.figure("Degree of a random graph", figsize=(8, 8))
# Create a gridspec for adding subplots of different sizes
axgrid = fig.add_gridspec(5, 4)

ax0 = fig.add_subplot(axgrid[0:3, :])
Gcc = G.subgraph(sorted(nx.connected_components(G), key=len, reverse=True)[0])
pos = nx.spring_layout(Gcc, seed=10396953)
nx.draw_networkx_nodes(Gcc, pos, ax=ax0, node_size=20)
nx.draw_networkx_edges(Gcc, pos, ax=ax0, alpha=0.4)
ax0.set_title("Connected components of G")
ax0.set_axis_off()

print("aa")

ax1 = fig.add_subplot(axgrid[3:, :2])
ax1.plot(degree_sequence, "b-", marker="o")
ax1.set_title("Degree Rank Plot")
ax1.set_ylabel("Degree")
ax1.set_xlabel("Rank")

ax2 = fig.add_subplot(axgrid[3:, 2:])
ax2.bar(*np.unique(degree_sequence, return_counts=True))
ax2.set_title("Degree histogram")
ax2.set_xlabel("Degree")
ax2.set_ylabel("# of Nodes")

fig.tight_layout()
plt.show()


class Game:
    def __init__(self):
        self.snake = Snake(400, 300, 5, 0)
        self.enemy = Enemy(100, 100, 3, 1)
        self.power_up = PowerUp(200, 200)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.snake.change_direction(0)
                elif event.key == pygame.K_DOWN:
                    self.snake.change_direction(1)
                elif event.key == pygame.K_LEFT:
                    self.snake.change_direction(2)
                elif event.key == pygame.K_RIGHT:
                    self.snake.change_direction(3)
        return True

    def update(self):
        self.snake.move()
        self.enemy.move()

    def draw(self, screen):
        self.snake.draw(screen)
        self.enemy.draw(screen)
        self.power_up.draw(screen)
