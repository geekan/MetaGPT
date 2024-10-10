# -*- coding: utf-8 -*-
import argparse
import asyncio
import json

from DABench import DABench

from metagpt.roles.di.data_interpreter import DataInterpreter


def init_agent(*args, **kwargs):
    return


async def get_prediction(agent_class, requirement):
    """Helper function to get prediction from a new instance of the agent"""
    try:
        agent = agent_class  # Instantiate the agent inside this function to avoid memory conflicts
        result = await agent.run(requirement)
        prediction_json = json.loads(str(result).split("Current Plan")[1].split("## Current Task")[0])
        prediction = prediction_json[-1]["result"]
        return prediction
    except Exception as e:
        print(f"Error processing requirement: {requirement}. Error: {e}")
        return None


async def evaluate_all(agent_class):
    """Evaluate all tasks in DABench using the specified baseline agent"""
    DA = DABench()
    id_list, predictions = [], []
    tasks = []
    for key, value in DA.answers.items():
        requirement = DA.get_prompt(key)
        tasks.append(get_prediction(agent_class, requirement))
        id_list.append(key)
    # Run all tasks concurrently
    predictions = await asyncio.gather(*tasks)
    # Filter out any None values in predictions
    predictions = [pred for pred in predictions if pred is not None]
    print(DA.eval_all(id_list, predictions))


def main():
    # Set up argparse to handle command-line arguments
    parser = argparse.ArgumentParser(description="Run evaluation with different baselines.")
    # Define the command-line argument for the agent name
    parser.add_argument(
        "--agent_name",
        type=str,
        default="DataInterpreter",
        help="Specify the baseline agent class to use for evaluation.",
    )
    # Parse the arguments
    args = parser.parse_args()
    # Manually match the agent name to the class
    if args.agent_name == "DataInterpreter":
        agent_class = DataInterpreter()
    # Add more agents as needed
    # elif args.agent_name == "OtherAgent":
    #     agent_class = OtherAgent
    else:
        print(f"Agent {args.agent_name} not recognized.")
        return
    # Run the evaluation with the specified agent class
    asyncio.run(evaluate_all(agent_class))


if __name__ == "__main__":
    main()
