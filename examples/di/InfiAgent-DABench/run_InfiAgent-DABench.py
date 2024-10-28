import asyncio
import json

from DABench import DABench

from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter


async def get_prediction(agent, requirement):
    """Helper function to obtain a prediction from a new instance of the agent.

    This function runs the agent with the provided requirement and extracts the prediction
    from the result. If an error occurs during processing, it logs the error and returns None.

    Args:
        agent: The agent instance used to generate predictions.
        requirement: The input requirement for which the prediction is to be made.

    Returns:
        The predicted result if successful, otherwise None.
    """
    try:
        # Run the agent with the given requirement and await the result
        result = await agent.run(requirement)

        # Parse the result to extract the prediction from the JSON response
        prediction_json = json.loads(str(result).split("Current Plan")[1].split("## Current Task")[0])
        prediction = prediction_json[-1]["result"]  # Extract the last result from the parsed JSON

        return prediction  # Return the extracted prediction
    except Exception as e:
        # Log an error message if an exception occurs during processing
        logger.info(f"Error processing requirement: {requirement}. Error: {e}")
        return None  # Return None in case of an error


async def evaluate_all(agent, k):
    """Evaluate all tasks in DABench using the specified baseline agent.

    Tasks are divided into groups of size k and processed in parallel.

    Args:
        agent: The baseline agent used for making predictions.
        k (int): The number of tasks to process in each group concurrently.
    """
    bench = DABench()  # Create an instance of DABench to access its methods and data
    id_list, predictions = [], []  # Initialize lists to store IDs and predictions
    tasks = []  # Initialize a list to hold the tasks

    # Iterate over the answers in DABench to generate tasks
    for key, value in bench.answers.items():
        requirement = bench.generate_formatted_prompt(key)  # Generate a formatted prompt for the current key
        tasks.append(get_prediction(agent, requirement))  # Append the prediction task to the tasks list
        id_list.append(key)  # Append the current key to the ID list

    # Process tasks in groups of size k and execute them concurrently
    for i in range(0, len(tasks), k):
        # Get the current group of tasks
        current_group = tasks[i : i + k]
        # Execute the current group of tasks in parallel
        group_predictions = await asyncio.gather(*current_group)
        # Filter out any None values from the predictions and extend the predictions list
        predictions.extend(pred for pred in group_predictions if pred is not None)

    # Evaluate the results using all valid predictions and logger.info the evaluation
    logger.info(bench.eval_all(id_list, predictions))


def main(k=5):
    """Main function to run the evaluation process."""
    agent = DataInterpreter()  # Create an instance of the DataInterpreter agent
    asyncio.run(evaluate_all(agent, k))  # Run the evaluate_all function asynchronously


if __name__ == "__main__":
    main()
