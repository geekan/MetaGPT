# InfiAgent-DABench
This example is used to solve the InfiAgent-DABench using Data Interpreter (DI), and obtains 94.93% accuracy using gpt-4o.

## Dataset download
```
cd /examples/di/InfiAgent-DABench
git clone https://github.com/InfiAgent/InfiAgent.git
mv InfiAgent/examples/DA-Agent/data ./
```
## Special note:
When doing DABench testing, you need to set the ExecuteNbCode() init to:
```
class ExecuteNbCode(Action):
    """execute notebook code block, return result to llm, and display it."""

    nb: NotebookNode
    nb_client: NotebookClient
    console: Console
    interaction: str
    timeout: int = 600

    def __init__(
        self,
        nb=nbformat.v4.new_notebook(),
        timeout=600,
    ):
        super().__init__(
            nb=nbformat.v4.new_notebook(),#nb,
            nb_client=NotebookClient(nb, timeout=timeout),
            timeout=timeout,
            console=Console(),
            interaction=("ipython" if self.is_ipython() else "terminal"),
        )
```
The path of ExecuteNbCode() is: 
```
metagpt.actions.di.execute_nb_code
```
Instead of using the original nb initialization by default.
## How to run
```
python run_InfiAgent-DABench_single.py --id x   # run a task, x represents the id of the question you want to test
python run_InfiAgent-DABench_all.py    # Run all tasks serially
python run_InfiAgent-DABench.py --k x    # Run all tasks in parallel, x represents the number of parallel tasks at a time
```