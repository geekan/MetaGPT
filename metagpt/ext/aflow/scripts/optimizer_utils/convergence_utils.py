# -*- coding: utf-8 -*-
# @Date    : 9/23/2024 10:00 AM
# @Author  : Issac
# @Desc    :

import json
import os

import numpy as np

from metagpt.logs import logger


class ConvergenceUtils:
    def __init__(self, root_path):
        self.root_path = root_path
        self.data = None
        self.rounds = None
        self.avg_scores, self.stds = None, None

    def load_data(self, root_path):
        """
        Read JSON file, create a new file if it doesn't exist, then return the data.
        """
        rounds_dir = os.path.join(root_path, "workflows")
        result_file = os.path.join(rounds_dir, "results.json")

        # Ensure directory exists
        os.makedirs(rounds_dir, exist_ok=True)

        # If file doesn't exist, create a new one with an empty list
        if not os.path.exists(result_file):
            with open(result_file, "w") as file:
                json.dump([], file)

        # Read file and return data
        with open(result_file, "r") as file:
            return json.load(file)

    def process_rounds(self):
        """
        Organize data by round, return a dictionary of scores by round.
        """
        self.data = self.load_data(root_path=self.root_path)
        rounds = {}
        for entry in self.data:
            round_number = entry["round"]
            score = entry["score"]
            if round_number not in rounds:
                rounds[round_number] = []
            rounds[round_number].append(score)
        return rounds

    def calculate_avg_and_std(self):
        """
        Calculate average score and standard deviation for each round, return two lists: average scores and standard deviations.
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
        Check for convergence. z is the z-score corresponding to the confidence level.
        consecutive_rounds is the number of consecutive rounds that must meet the stop condition.
        """
        # Calculate average score and standard deviation for each round
        self.avg_scores, self.stds = self.calculate_avg_and_std()
        # If total rounds are not enough to calculate top_k+1 rounds, return not converged
        if len(self.avg_scores) < top_k + 1:
            return False, None, None
        convergence_count = 0  # Convergence counter
        previous_y = None  # Y value of the previous round (average of top_k scores)
        sigma_y_previous = None  # Standard error of Y value from previous round
        for i in range(len(self.avg_scores)):
            # Dynamically select top_k from current round and all previous rounds
            top_k_indices = np.argsort(self.avg_scores[: i + 1])[::-1][
                :top_k
            ]  # Select top k indices by descending average score
            top_k_scores = [self.avg_scores[j] for j in top_k_indices]  # Get list of top k scores
            top_k_stds = [
                self.stds[j] for j in top_k_indices
            ]  # Get list of standard deviations corresponding to top k scores
            # Calculate mean of top k scores for current round, i.e., y_current
            y_current = np.mean(top_k_scores)
            # Calculate standard error of y_current (sigma_y_current), representing score dispersion
            sigma_y_current = np.sqrt(np.sum([s**2 for s in top_k_stds]) / (top_k**2))
            # If not the first round, calculate change in Y (Delta_Y) and corresponding standard error
            if previous_y is not None:
                # Calculate Y difference between current round and previous round
                delta_y = y_current - previous_y
                # Calculate standard error of Y difference (sigma_Delta_Y)
                sigma_delta_y = np.sqrt(sigma_y_current**2 + sigma_y_previous**2)
                # Check if Y change is within acceptable confidence interval, i.e., convergence condition
                if abs(delta_y) <= z * sigma_delta_y:
                    convergence_count += 1
                    # If consecutive converged rounds reach set value, return convergence information
                    if convergence_count >= consecutive_rounds:
                        return True, i - consecutive_rounds + 1, i
                else:
                    # If change is large, reset convergence counter
                    convergence_count = 0
            # Update Y value and standard error for previous round
            previous_y = y_current
            sigma_y_previous = sigma_y_current
        # If convergence condition not met, return not converged
        return False, None, None

    def print_results(self):
        """
        Print average score and standard deviation for all rounds.
        """
        self.avg_scores, self.stds = self.calculate_avg_and_std()
        for i, (avg_score, std) in enumerate(zip(self.avg_scores, self.stds), 1):
            logger.info(f"Round {i}: Average Score = {avg_score:.4f}, Standard Deviation = {std:.4f}")


if __name__ == "__main__":
    # Use this class and specify top_k
    checker = ConvergenceUtils("path")  # For example, set top_k=5
    converged, convergence_round, final_round = checker.check_convergence()

    if converged:
        logger.info(f"Convergence detected, occurred at round {convergence_round}, final round is {final_round}")
    else:
        logger.info("No convergence detected within all rounds")

    # Print average score and standard deviation for each round
    checker.print_results()
