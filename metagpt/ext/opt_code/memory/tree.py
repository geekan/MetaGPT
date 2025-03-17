from abc import ABC, abstractmethod
from pydantic import BaseModel

import os
import pickle
import json

class TreeNode(ABC, BaseModel):
    code: str | list[str] = None
    reward: float = -1
    children: list['TreeNode'] = []
    parent: 'TreeNode' = None
    depth: int = None
    id: str = None
    visited: bool = False

    @abstractmethod
    def update_from_child(self, child):
        pass

    @abstractmethod
    def update_from_results(self, results):
        pass

    def save_node(self, path):
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, f"Node_{self.id}.pkl"), "wb") as f:
            pickle.dump(self, f)

    @abstractmethod
    def extend_child(self, action):
        pass



class Tree(ABC, BaseModel):
    root_path: str = None
    root_node: TreeNode = None
    node_list: list = []

    def initialize(self, args, root_path):
        self.root_node = self.init_root_node(args)
        self.root_path = root_path
        self.node_list.append(self.root_node)

        return self.root_node

    @abstractmethod
    def init_root_node(self, args):
        pass

    # @abstractmethod
    # def select(self) -> TreeNode:
    #     """
    #         Select a node from the memory to process.
    #     """
    #     pass

    def update_from_child(self, node: TreeNode, results):
        """
        Update the parent node with the results of the child node.
        
        Args:
            node: The parent node to update
            results: Dictionary containing the results of the child node
        """
        node.update_from_results(results)
        parent = node.parent
        child = node
        while parent:
            parent.update_from_child(child)
            child = parent
            parent = parent.parent

    def report(tree, output_file=None, detailed=False):
        """
        Generate a report of all nodes in the tree structure and optionally save it to a file.
        
        Args:
            tree: An instance of a Tree class containing nodes to report on
            output_file: Optional path to save the report (if None, only prints to console)
            detailed: If True, includes more detailed information for each node
        
        Returns:
            str: The formatted report text
        """
        if not tree.root_node:
            return "Tree is empty, no nodes to report."
        
        report_text = []
        report_text.append("=" * 80)
        report_text.append(f"TREE REPORT - Total Nodes: {len(tree.node_list)}")
        report_text.append("=" * 80)
                
        # Using BFS to traverse the tree
        queue = [(tree.root_node, 0)]  # (node, level)
        visited = set()
        
        while queue:
            node, level = queue.pop(0)
            if node.id in visited:
                continue
                
            visited.add(node.id)
            
            # Format node information
            node_info = []
            indent = "  " * level
            node_info.append(f"{indent}Node ID: {node.id} (Depth: {node.depth})")
            node_info.append(f"{indent}Reward: {node.reward}")
            node_info.append(f"{indent}Visited: {node.visited}")
            
            # Add specific information for AFlowNode if applicable
            if hasattr(node, 'modification_info') and node.modification_info:
                node_info.append(f"{indent}Modification: {node.modification_info}")
            
            if hasattr(node, 'experience'):
                node_info.append(f"{indent}Experience:")
                if node.experience.get("success"):
                    node_info.append(f"{indent}  Success: {len(node.experience['success'])} records")
                if node.experience.get("failure"):
                    node_info.append(f"{indent}  Failure: {len(node.experience['failure'])} records")
            
            if hasattr(node, 'log_data') and node.log_data:
                node_info.append(f"{indent}Log entries: {len(node.log_data)}")
            
            # Add specific information for SelaNode if applicable
            if hasattr(node, 'visit_count'):
                node_info.append(f"{indent}Visit count: {node.visit_count}")
            
            if hasattr(node, 'normalized_reward'):
                node_info.append(f"{indent}Normalized rewards:")
                for key, value in node.normalized_reward.items():
                    node_info.append(f"{indent}  {key}: {value}")
            
            if hasattr(node, 'raw_reward') and node.raw_reward:
                node_info.append(f"{indent}Raw rewards:")
                for key, value in node.raw_reward.items():
                    node_info.append(f"{indent}  {key}: {value}")
            
            if hasattr(node, 'raw_value'):
                node_info.append(f"{indent}Raw value: {node.raw_value}")
                
            if hasattr(node, 'action') and node.action:
                node_info.append(f"{indent}Action: {node.action}")
                
            if hasattr(node, 'tasks') and node.tasks:
                node_info.append(f"{indent}Tasks: {len(node.tasks)} tasks")
                if detailed:
                    for i, task in enumerate(node.tasks):
                        node_info.append(f"{indent}  Task {i+1}: {task[:50]}..." if len(task) > 50 else f"{indent}  Task {i+1}: {task}")
                        
            if hasattr(node, 'outputs') and node.outputs:
                node_info.append(f"{indent}Outputs: {len(node.outputs)} outputs")
                if detailed:
                    for i, output in enumerate(node.outputs):
                        node_info.append(f"{indent}  Output {i+1}: {output[:50]}..." if len(output) > 50 else f"{indent}  Output {i+1}: {output}")
                        
            if hasattr(node, 'role_path') and node.role_path:
                node_info.append(f"{indent}Role path: {node.role_path}")
                
            if hasattr(node, 'state_saved'):
                node_info.append(f"{indent}State saved: {node.state_saved}")
            
            # Code snippet (truncated if too long)
            if node.code:
                if isinstance(node.code, list):
                    code_sample = str(node.code[:2]) + "..." if len(node.code) > 2 else str(node.code)
                    node_info.append(f"{indent}Code (list, {len(node.code)} items): {code_sample}")
                else:
                    code_lines = node.code.split('\n')
                    code_sample = '\n'.join(code_lines[:3]) + "..." if len(code_lines) > 3 else node.code
                    node_info.append(f"{indent}Code (truncated): {code_sample}")
                    
            # State information for SelaNode (truncated)
            if hasattr(node, 'state') and node.state and detailed:
                state_str = json.dumps(node.state, indent=2)
                state_lines = state_str.split('\n')
                state_sample = '\n'.join(state_lines[:5]) + "..." if len(state_lines) > 5 else state_str
                node_info.append(f"{indent}State (truncated): {state_sample}")
            
            # Children information
            node_info.append(f"{indent}Children: {len(node.children)}")
            
            # Add to report
            report_text.append("\n".join(node_info))
            report_text.append("-" * 40)
            
            # Add children to queue
            for child in node.children:
                queue.append((child, level + 1))
        
        # Add tree-specific statistics at the end
        report_text.append("=" * 80)
        report_text.append("TREE STATISTICS")
        report_text.append("=" * 80)
        
        # Add stats for each tree type
        if isinstance(tree, Tree):
            max_depth = max([node.depth for node in tree.node_list]) if tree.node_list else 0
            report_text.append(f"Maximum depth: {max_depth}")
            
            # For SelaMemory
            if hasattr(tree, 'c_explore'):
                report_text.append(f"Exploration constant (c_explore): {tree.c_explore}")
                report_text.append(f"Unvisited constant (c_unvisited): {tree.c_unvisited}")
                report_text.append(f"Current node pointer: {tree.node_pointer}")
            
            # For AFlowMemory
            if hasattr(tree, 'k_selected'):
                report_text.append(f"K selected: {tree.k_selected}")
        
        # Compile full report
        full_report = "\n".join(report_text)
        
        # Print report
        print(full_report)
        
        # Save to file if requested
        if output_file:
            with open(output_file, "w") as f:
                f.write(full_report)
            print(f"Report saved to {output_file}")
        
        return full_report