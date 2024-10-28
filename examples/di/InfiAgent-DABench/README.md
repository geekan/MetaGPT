# InfiAgent-DABench
This example is used to solve the InfiAgent-DABench using Data Interpreter (DI), and obtains 94.93% accuracy using gpt-4o.

## Dataset
```
cd /examples/di/InfiAgent-DABench
git clone https://github.com/InfiAgent/InfiAgent.git
mv InfiAgent/examples/DA-Agent/data ./
```
## How to run
```
python run_InfiAgent-DABench_single.py --id x   # run a task, x represents the id of the question you want to test
python run_InfiAgent-DABench_all.py    # Run all tasks serially
python run_InfiAgent-DABench.py --k x    # Run all tasks in parallel, x represents the number of parallel tasks at a time
```