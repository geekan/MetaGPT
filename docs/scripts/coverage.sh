coverage run --source ./metagpt -m pytest --durations=0 && coverage report -m && coverage html && open htmlcov/index.html
