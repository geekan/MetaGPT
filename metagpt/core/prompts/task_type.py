# Prompt for taking on "eda" tasks
EDA_PROMPT = """
The current task is about exploratory data analysis, please note the following:
- Distinguish column types with `select_dtypes` for tailored analysis and visualization, such as correlation.
- Remember to `import numpy as np` before using Numpy functions.
"""

# Prompt for taking on "data_preprocess" tasks
DATA_PREPROCESS_PROMPT = """
The current task is about data preprocessing, please note the following:
- Monitor data types per column, applying appropriate methods.
- Ensure operations are on existing dataset columns.
- Avoid writing processed data to files.
- **ATTENTION** Do NOT make any changes to the label column, such as standardization, etc.
- Prefer alternatives to one-hot encoding for categorical data.
- Only encode or scale necessary columns to allow for potential feature-specific engineering tasks (like time_extract, binning, extraction, etc.) later.
- Each step do data preprocessing to train, must do same for test separately at the same time.
- Always copy the DataFrame before processing it and use the copy to process.
"""

# Prompt for taking on "feature_engineering" tasks
FEATURE_ENGINEERING_PROMPT = """
The current task is about feature engineering. when performing it, please adhere to the following principles:
- Generate as diverse features as possible to improve the model's performance step-by-step. 
- Use available feature engineering tools if they are potential impactful.
- Avoid creating redundant or excessively numerous features in one step.
- Exclude ID columns from feature generation and remove them.
- Each feature engineering operation performed on the train set must also applies to the dev/test separately at the same time.
- **ATTENTION** Do NOT use the label column to create features, except for cat encoding.
- Use the data from previous task result if exist, do not mock or reload data yourself.
- Always copy the DataFrame before processing it and use the copy to process.
"""

# Prompt for taking on "model_train" tasks
MODEL_TRAIN_PROMPT = """
The current task is about training a model, please ensure high performance:
- For tabular datasets - you have access to XGBoost, CatBoost, random forest, extremely randomized trees, k-nearest neighbors, linear regression, etc.
- For image datasets - you have access to Swin Transformer, ViT, ResNet, EfficientNet, etc.
- For text datasets - you have access to Electra, DeBERTa, GPT-2, BERT, etc.
- Avoid the use of SVM because of its high training time.
- Keep in mind that your user prioritizes results and is highly focused on model performance. So, when needed, feel free to use models of any complexity to improve effectiveness, such as XGBoost, CatBoost, etc.
- If non-numeric columns exist, perform label encode together with all steps.
- Use the data from previous task result directly, do not mock or reload data yourself.
- Set suitable hyperparameters for the model, make metrics as high as possible.
"""

# Prompt for taking on "model_evaluate" tasks
MODEL_EVALUATE_PROMPT = """
The current task is about evaluating a model, please note the following:
- Ensure that the evaluated data is same processed as the training data. If not, remember use object in 'Done Tasks' to transform the data.
- Use trained model from previous task result directly, do not mock or reload model yourself.
"""

# Prompt for taking on "image2webpage" tasks
IMAGE2WEBPAGE_PROMPT = """
The current task is about converting image into webpage code. please note the following:
- Single-Step Code Generation: Execute the entire code generation process in a single step, encompassing HTML, CSS, and JavaScript. Avoid fragmenting the code generation into multiple separate steps to maintain consistency and simplify the development workflow.
- Save webpages: Be sure to use the save method provided.
"""

# Prompt for taking on "web_scraping" tasks
WEB_SCRAPING_PROMPT = """
- Remember to view and print the necessary HTML content in a separate task to understand the structure first before scraping data. Such as `html_content = await view_page_element_to_scrape(...)\nprint(html_content)`.
- Since the data required by user may not correspond directly to the actual HTML element names, you should thoroughly analyze the HTML structure and meanings of all elements in your context first. Ensure the `class_` in your code should derived from the actual HTML structure directly, not based on your knowledge. To ensure it, analyse the most suitable location of the 'class_' in the actual HTML content before code.
- Reuse existing html object variable from previous code (if any) to extract data, do not mock or hard code a html variable yourself.
"""
