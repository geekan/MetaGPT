
## Run MetaGPT MLEngineer to solve math problems

- Use `--categories` to select category to run, The problems are randomly selected from level-5 difficulty. Here are the category names and IDs:

| ID | Category Name            |
|----|--------------------------|
| 0  | Algebra                  |
| 1  | Counting & Probability   |
| 2  | Geometry                 |
| 3  | Intermediate Algebra     |
| 4  | Number Theory            |
| 5  | Prealgebra               |
| 6  | Precalculus              |


- Download the [**MATH dataset here**](https://people.eecs.berkeley.edu/~hendrycks/MATH.tar)


- Extract the tar file to `./MATH`

  
- Test on level-5 problem from Number Theory (`--categories 4`):

```python
python main.py --categories 4 --level 5 --vote_num 3 --folder ./math_experiment --dataset_path ./MATH
```
You can find the experiment records in folder `./math_experiment`.

