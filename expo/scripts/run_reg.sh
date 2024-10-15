#!/bin/bash

tasks=("concrete-strength" "Moneyball" "colleges" "SAT11-HAND-runtime-regression" "diamonds" "boston" "house-prices")

for i in {1..3}
do
    for task in "${tasks[@]}"; do
        echo "Running experiment for task: $task"
        python run_experiment.py --exp_mode mcts --task "$task" --rollouts 10 --low_is_better --special_instruction stacking
        echo "Experiment for task $task completed."
    done
done

echo "All experiments completed."
