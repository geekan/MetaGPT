# -*- coding: utf-8 -*-
# @Date    : 9/23/2024 10:00 AM
# @Author  : Issac
# @Desc    : 

import numpy as np
import json
import os
from metagpt.logs import logger

class ConvergenceUtils:
    def __init__(self, root_path):
        self.root_path = root_path
        self.data = None
        self.rounds = None
        self.avg_scores, self.stds = None, None

    def load_data(self, root_path):
        """
        读取 JSON 文件，如果不存在则创建一个新文件，然后返回数据。
        """
        rounds_dir = os.path.join(root_path, "workflows")
        result_file = os.path.join(rounds_dir, "results.json")

        # 确保目录存在
        os.makedirs(rounds_dir, exist_ok=True)

        # 如果文件不存在，创建一个包含空列表的新文件
        if not os.path.exists(result_file):
            with open(result_file, 'w') as file:
                json.dump([], file)

        # 读取文件并返回数据
        with open(result_file, 'r') as file:
            return json.load(file)

    def process_rounds(self):
        """
        以 round 为单位组织数据，返回按轮次的分数字典。
        """
        self.data = self.load_data(root_path=self.root_path)
        rounds = {}
        for entry in self.data:
            round_number = entry['round']
            score = entry['score']
            if round_number not in rounds:
                rounds[round_number] = []
            rounds[round_number].append(score)
        return rounds

    def calculate_avg_and_std(self):
        """
        计算每轮的平均分和标准差，返回两个列表：平均分和标准差。
        """
        self.rounds = self.process_rounds()

        sorted_rounds = sorted(self.rounds.items(), key=lambda x: x[0])
        avg_scores = []
        stds = []
        for round_number, scores in sorted_rounds:
            avg_scores.append(np.mean(scores))
            stds.append(np.std(scores))
        return avg_scores, stds

    def check_convergence(self, top_k=3, z=0, consecutive_rounds=5):
        """
        检查收敛的函数。z 为置信水平对应的 z 分数 。
        consecutive_rounds 为连续轮次内满足停止条件的次数。
        """
        self.avg_scores, self.stds = self.calculate_avg_and_std()

        if len(self.avg_scores) < top_k + 1:
            return False, None, None

        convergence_count = 0
        previous_Y = None
        sigma_Y_previous = None

        for i in range(len(self.avg_scores)):
            # 动态选择当前轮次及之前所有轮次的 top_k
            top_k_indices = np.argsort(self.avg_scores[:i + 1])[::-1][:top_k]
            top_k_scores = [self.avg_scores[j] for j in top_k_indices]
            top_k_stds = [self.stds[j] for j in top_k_indices]

            Y_current = np.mean(top_k_scores)
            sigma_Y_current = np.sqrt(np.sum([s ** 2 for s in top_k_stds]) / (top_k ** 2))

            if previous_Y is not None:
                Delta_Y = Y_current - previous_Y
                sigma_Delta_Y = np.sqrt(sigma_Y_current ** 2 + sigma_Y_previous ** 2)

                if abs(Delta_Y) <= z * sigma_Delta_Y:
                    convergence_count += 1
                    if convergence_count >= consecutive_rounds:
                        return True, i - consecutive_rounds + 1, i
                else:
                    convergence_count = 0

            previous_Y = Y_current
            sigma_Y_previous = sigma_Y_current

        return False, None, None

    def print_results(self):
        """
        打印所有轮次的平均分和标准差。
        """
        self.avg_scores, self.stds = self.calculate_avg_and_std()
        for i, (avg_score, std) in enumerate(zip(self.avg_scores, self.stds), 1):
            logger.info(f"轮次 {i}: 平均分 = {avg_score:.4f}, 标准差 = {std:.4f}")

if __name__ == "__main__":

    # 使用该类，并指定 top_k
    checker = ConvergenceUtils("path")  # 例如设置 top_k=5
    converged, convergence_round, final_round = checker.check_convergence()

    if converged:
        logger.info(f"检测到收敛，发生在第 {convergence_round} 轮，最终轮次为 {final_round} 轮")
    else:
        logger.info("在所有轮次内未检测到收敛")

    # 打印每轮的平均分和标准差
    checker.print_results()
