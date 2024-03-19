# Dataset Description

The index of sub_swebench is a subset of swebench, with two columns in total, each column containing 50 id_instance.

The id_instance is a balanced subset of pass and fail samples for CognitionAI on swebench.

The index of  scikit-learn-68 is another subset of CognitionAI in swebench (all tasks of the scikit-learn type), with a total of two columns：

- pass：12 
- fail：56

Sampling list:https://github.com/CognitionAI/devin-swebench-results/tree/main/
Original dataset：https://huggingface.co/datasets/princeton-nlp/SWE-bench/

## fail dataset Description：

There are a total of 491 txt files listed.
In the original dataset, the distribution of pass case categories is:

- astropy: 24
- django: 160
- matplotlib: 42
- mwaskom: 4
- pallets: 3
- psf: 9
- pydata: 29
- pylint-dev: 13
- pytest-dev: 20
- scikit-learn: 56
- sphinx-doc: 46
- sympy: 85

### After balanced sampling:

There are a total of 50 txt files listed.

- Django: 16
- Scikit-Learn: 6
- Sympy: 10
- sphinx-doc:5
- matplotlib: 4
- pydata: 3
- astropy: 2
- pytest-dev: 2
- psf: 1
- pylint-dev: 1



## pass dataset Description：



There are a total of 79 txt files listed.
In the original dataset, the distribution of pass case categories is:

- astropy: 4
- django: 38
- matplotlib: 3
- pydata: 3
- pytest-dev: 6
- scikit-learn: 12
- sphinx-doc: 2
- sympy: 11

### After balanced sampling:

There are a total of 50 txt files listed.

- Django: 23
- Scikit-Learn: 8
- Sympy: 7
- Pytest: 4
- Astropy: 3
- Xarray (pydata): 2
- Matplotlib: 2
- Sphinx: 1



##  scikit-learn-68 dataset Description：

instance_id_pass:12

instance_id_fail:56
