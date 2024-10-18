#!/bin/bash

tasks=("banking77" "gnad10" "sms_spam" "oxford-iiit-pet" "stanford_cars" "fashion_mnist" )

for i in {1..3}
do
    for task in "${tasks[@]}"; do
        echo "Running experiment for task: $task"
        python run_experiment.py --exp_mode mcts --task "$task" --rollouts 10
        echo "Experiment for task $task completed."
    done
done
echo "All experiments completed."
