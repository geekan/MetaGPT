SUBMISSION_INSTURCTION = """
- **Submission checker**: We provide a tool for checking the validity of your submission file, in the form of a server endpoint at `http://localhost:5000/validate`. If you post a submission file to the server (e.g. `curl -X POST -F "file=@${SUBMISSION_FILE}" ${SERVER_URL}`), you will receive a response message telling you if your submission is valid or not (note that this does NOT give you a score). For your convenience, we provide a script `/home/validate_submission.sh` which can help you make this submission to the validation server.
"""
INSTRUCTIONS = """
You are participating in *MLE-bench*, an offline version of Kaggle competitions adapted to test the coding ability of agents like yourself.

You will be given a machine learning task. You must solve the task by training a model and running the model on the test set to produce a submission file. You may not hand-label the data to produce a submission file.

BENCHMARK INSTRUCTIONS
------
First, please read the instructions below which are specific to our benchmark setup. Note, these instructions can be found again in `runner/mle_bench/instructions.py`.

- **Competition-specific instructions**: The instructions for the competition are available in `{dataset_dir}/description.md`. Read this file to understand the problem setup for the competition you are currently solving.
- **Dataset**: The dataset files for the competition are available in `{dataset_dir}`.
- **Submission**: We have simplified all competition types to use a simple CSV submission format. Regardless of what the competition instructions say, you MUST produce a submission file at `{output_dir}/submission.csv`. We will only evaluate submissions found at this path; failure to submit a `submission.csv` at this path will result in a failed attempt.
- **Test set**: In general, since we do not have access to the original test labels, we have constructed our own train/test split for each competition. As such, the dataset you see in `{dataset_dir}` may differ slightly from what is described in the competition instructions. Nevertheless the files available to you should otherwise be similar to the original and you should proceed with the competition task on the train/test splits available to you.
- **Cheating**: You are not allowed to view others' solutions to this competition. If we detect that your submission is plagiarized from others, the submission will be disqualified.

Your submission will be graded based on the metric in the competition-specific instructions. Your goal is to achieve the best score possible on the competition task. 

Wherever there is a conflict between the points above and the competition-specific instructions in `{dataset_dir}/description.md`, the above points should always take priority since these are always true for our offline benchmark setup.
"""

INSTRUCTIONS_OBFUSCATED = """
You are participating in *MLE-bench*, a benchmark designed to test the coding ability of agents like yourself.

You will be given a machine learning task. You must solve the task by training a model and running the model on the test set to produce a submission file. You may not hand-label the data to produce a submission file.

BENCHMARK INSTRUCTIONS
------
First, please read the instructions below which are specific to our benchmark setup. Note, these instructions can be found again in `runner/mle_bench/instructions.py`.

- **Task-specific instructions**: The instructions for the task are available in `{dataset_dir}/description.md`. Read this file to understand the problem setup for the task you are currently solving.
- **Dataset**: The dataset files for the task are available in `{dataset_dir}/`.
- **Submission**: Regardless of what the task instructions say, you MUST produce a submission file at `{output_dir}/submission.csv`. We will only evaluate submissions found at this path; failure to submit a `submission.csv` at this path will result in a failed attempt.
- **Test set**: In general, since we do not have access to the original test labels, we have constructed our own train/test split for each task. As such, the dataset you see in `{dataset_dir}` may differ slightly from what is described in the task instructions. Nevertheless the files available to you should otherwise be similar to the original and you should proceed with the task on the train/test splits available to you.
- **Cheating**: You are not allowed to view others' solutions to this task. If we detect that your submission is plagiarized from others, the submission will be disqualified.

Your submission will be graded based on the metric in the task-specific instructions. Your goal is to achieve the best score possible on the task. 

Wherever there is a conflict between the points above and the task-specific instructions in `{dataset_dir}/description.md`, the above points should always take priority since these are always true for our offline benchmark setup.
"""

ADDITIONAL_NOTES = """
ADDITIONAL NOTES
------
- **Compute**: You have access to gpu with the appropriate drivers installed.
"""
