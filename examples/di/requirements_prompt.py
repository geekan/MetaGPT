# ML-Benchmark requirements
IRIS_REQ = "Run data analysis on sklearn Iris dataset, include a plot"
WINES_RECOGNITION_REQ = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class with 20% as test set, and show prediction accuracy"
BREAST_CANCER_WISCONSIN_REQ = "Run data analysis on sklearn Wisconsin Breast Cancer dataset, include a plot, train a model to predict targets (20% as validation), and show validation accuracy"
TITANIC_REQ = "This is a titanic passenger survival dataset, your goal is to predict passenger survival outcome. The target column is Survived. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report accuracy on the eval data. Train data path: '{data_dir}/di_dataset/ml_benchmark/04_titanic/split_train.csv', eval data path: '{data_dir}/di_dataset/ml_benchmark/04_titanic/split_eval.csv'."
HOUSE_PRICES_ADVANCED_REGRESSION_TECHNIQUES_REQ = "This is a house price dataset, your goal is to predict the sale price of a property based on its features. The target column is SalePrice. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report RMSE between the logarithm of the predicted value and the logarithm of the observed sales price on the eval data. Train data path: '{data_dir}/di_dataset/ml_benchmark/05_house-prices-advanced-regression-techniques/split_train.csv', eval data path: '{data_dir}/di_dataset/ml_benchmark/05_house-prices-advanced-regression-techniques/split_eval.csv'."
SANTANDER_CUSTOMER_TRANSACTION_PREDICTION_REQ = "This is a customers financial dataset. Your goal is to predict which customers will make a specific transaction in the future. The target column is target. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report AUC on the eval data. Train data path: '{data_dir}/di_dataset/ml_benchmark/06_santander-customer-transaction-prediction/split_train.csv', eval data path: '{data_dir}/di_dataset/ml_benchmark/06_santander-customer-transaction-prediction/split_eval.csv' ."
ICR_IDENTITY_AGE_RELATED_CONDITIONS_REQ = "This is a medical dataset with over fifty anonymized health characteristics linked to three age-related conditions. Your goal is to predict whether a subject has or has not been diagnosed with one of these conditions. The target column is Class. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report F1 Score on the eval data. Train data path: '{data_dir}/di_dataset/ml_benchmark/07_icr-identify-age-related-conditions/split_train.csv', eval data path: '{data_dir}/di_dataset/ml_benchmark/07_icr-identify-age-related-conditions/split_eval.csv' ."
SANTANDER_VALUE_PREDICTION_CHALLENGE_REQ = "This is a customers financial dataset. Your goal is to predict the value of transactions for each potential customer. The target column is target. Perform data analysis, data preprocessing, feature engineering, and modeling to predict the target. Report RMSLE on the eval data. Train data path: '{data_dir}/di_dataset/ml_benchmark/08_santander-value-prediction-challenge/split_train.csv', eval data path: '{data_dir}/di_dataset/ml_benchmark/08_santander-value-prediction-challenge/split_eval.csv' ."

# Open-Ended Tasks requirements
OCR_REQ_01 = "This is an English invoice image. Your goal is to perform OCR on the image, extract the total amount from ocr result and save as table, using PaddleOCR. The PaddleOCR environment has been fully installed, try to use Paddleocr as much as possible. Image path: '{data_dir}/di_dataset/open_ended_tasks/01_ocr.png"
OCR_REQ_02 = "This is a Chinese invoice image. Your goal is to perform OCR on the image and only output the recognized text word results, nothing else is needed, then extract the total amount and receipt ID starting with 'No' from ocr text words results and save as table, using PaddleOCR. The PaddleOCR environment has been fully installed, try to use Paddleocr as much as possible. Image path: '{data_dir}/di_dataset/open_ended_tasks/02_ocr.jpg"
OCR_REQ_03 = "This is an invoice image for OCR. Your goal is to perform OCR on the image, extract the total amount and save it into an Excel table format, using PaddleOCR with lang='en' The PaddleOCR environment has been fully installed, try to use Paddleocr as much as possible. Image path: '{data_dir}/di_dataset/open_ended_tasks/03_ocr.jpg"
WEB_SEARCH_AND_CRAWLING_REQ_04 = "Get data from `paperlist` table in https://papercopic.com/statistics/iclr-statistics/iclr-2024-statistics/ , and save it to a csv file. paper title must include `multiagent` or `large language model`. **notice: print key variables**"
WEB_SEARCH_AND_CRAWLING_REQ_05 = "Obtain the CPI data from https://www.stats.gov.cn/sj/sjjd/202307/t20230718_1941322.html, please follow this plan step by step: 1. Detect the encoding type and HTML structure of the target webpage. 2. Crawl the webpage, de-duplicate the body content, convert it to a clear paragraph suitable for reading as plain text, and save it to target.txt. 3. Design multiple regular expressions to match key sentences in target.txt, use try-except statements to combine the various regular expression matches, note that the webpage text is in Chinese. 4. Finally, use a Chinese summary to summarize the key sentences to answer the user's request. **Note: If it is a code block, print out the key variable results of the code block; if it is webpage text, print the first 200 characters.**"
WEB_SEARCH_AND_CRAWLING_REQ_06 = "Get products data from website https://scrapeme.live/shop/ and save it as a csv file. Notice: Firstly parse the web page encoding and the text HTML structure; The first page product name, price, product URL, and image URL must be saved in the csv;"
WEB_SEARCH_AND_CRAWLING_REQ_07 = "从36kr创投平台https://pitchhub.36kr.com/financing-flash所有初创企业融资的信息, **注意: 这是⼀个中⽂⽹站**; 下⾯是⼀个⼤致流程, 你会根据每⼀步的运⾏结果对当前计划中的任务做出适当调整: 1. 爬取并本地保存html结构; 2. 直接打印第7个**快讯**关键词后2000个字符的html内容, 作为**快讯的html内容示例**; 3. 反思**快讯的html内容示例**中的规律, 设计正则匹配表达式来获取**快讯**的标题、链接、时间; 4. 筛选最近3天的初创企业融资**快讯**, 以list[dict]形式打印前5个。5. 将全部结果存在本地csv中"
EMAIL_REPLY_REQ_08 = """You are an agent that automatically reads and replies to emails. I will give you your Outlook email account and password. You need to check the content of the latest email and return it to me. If the email address suffix of this email is @xxx.xxx, please automatically reply with "I've received your email and will reply as soon as possible. Thank you!" Email account: xxx@xxx.xxx Email Password: xxxx"""
WEB_PAGE_IMITATION_REQ_09 = "This is a URL of webpage: https://medium.com/ . Firstly, utilize Selenium and WebDriver for rendering. Secondly, convert image to a webpage including HTML, CSS and JS in one go. Finally, save webpage in a text file. All required dependencies and environments have been fully installed and configured."
WEB_PAGE_IMITATION_REQ_10 = "This is a URL of webpage: https://pytorch.org/ . Firstly, utilize Selenium and WebDriver for rendering. Secondly, convert image to a webpage including HTML, CSS and JS in one go. Finally, save webpage in a file. NOTE: All required dependencies and environments have been fully installed and configured."
WEB_PAGE_IMITATION_REQ_11 = "This is a URL of webpage: https://www.kaggle.com/ . Firstly, utilize Selenium and WebDriver to render the webpage, ensuring the browser window is maximized for an optimal viewing experience. Secondly, convert image to a webpage including HTML, CSS and JS in one go. Finally, save webpage in a file. NOTE: All required dependencies and environments have been fully installed and configured."
WEB_PAGE_IMITATION_REQ_12 = "This is a URL of webpage: https://chat.openai.com/auth/login . Firstly, utilize Selenium and WebDriver to render the webpage, ensuring the browser window is maximized for an optimal viewing experience. Secondly, convert image to a webpage including HTML, CSS and JS in one go. Finally, save webpage in a file. NOTE: All required dependencies and environments have been fully installed and configured."
WEB_PAGE_IMITATION_REQ_13 = "This is a URL of webpage: https://deepmind.google/technologies/gemini/#introduction . Firstly, utilize Selenium and WebDriver to render the webpage, ensuring the browser window is maximized for an optimal viewing experience. Secondly, convert image to a webpage including HTML, CSS and JS in one go. Finally, save webpage in a file. NOTE: All required dependencies and environments have been fully installed and configured."
IMAGE_BACKGROUND_REMOVAL_REQ_14 = "This is an image, you need to use python toolkit rembg remove the background of the image. image path:'{data_dir}/di_dataset/open_ended_tasks/14_image_background_removal.jpg'; save path:'{data_dir}/di_dataset/open_ended_tasks/14_image_background_removal_result.jpg'"
TEXT2IMG_REQ_15 = """I want to generate an image of a beautiful girl using the stable diffusion text2image tool, sd_url = 'http://your.sd.service.ip:port'"""
IMAGE2CODE_GENERATION_REQ_16 = "This is a image. First, convert the image to webpage code including HTML, CSS and JS in one go, and finally save webpage code in a file.The image path: '{data_dir}/di_dataset/open_ended_tasks/16_image_2_code_generation.png'. NOTE: All required dependencies and environments have been fully installed and configured."
IMAGE2CODE_GENERATION_REQ_17 = "This is a image. First, convert the image to webpage code including HTML, CSS and JS in one go, and finally save webpage code in a file.The image path: '{data_dir}/di_dataset/open_ended_tasks/17_image_2_code_generation.png'. NOTE: All required dependencies and environments have been fully installed and configured."
GENERATE_GAMES_REQ_18 = "Create a Snake game. Players need to control the movement of the snake to eat food and grow its body, while avoiding the snake's head touching their own body or game boundaries. Games need to have basic game logic, user interface. During the production process, please consider factors such as playability, beautiful interface, and convenient operation of the game. Note: pyxel environment already satisfied"
GENERATE_GAMES_REQ_19 = "You are a professional game developer, please use pyxel software to create a simple jumping game. The game needs to include a character that can move left and right on the screen. When the player presses the spacebar, the character should jump. Please ensure that the game is easy to operate, with clear graphics, and complies with the functional limitations of pyxel software. Note: pyxel environment already satisfied"
GENERATE_GAMES_REQ_20 = "Create a Snake game. Players need to control the movement of the snake to eat food and grow its body, while avoiding the snake's head touching their own body or game boundaries. Games need to have basic game logic, user interface. During the production process, please consider factors such as playability, beautiful interface, and convenient operation of the game. Note: pyxel environment already satisfied"

ML_BENCHMARK_REQUIREMENTS = {
    "01_iris": IRIS_REQ,
    "02_wines_recognition": WINES_RECOGNITION_REQ,
    "03_breast_cancer": BREAST_CANCER_WISCONSIN_REQ,
    "04_titanic": TITANIC_REQ,
    "05_house_prices": HOUSE_PRICES_ADVANCED_REGRESSION_TECHNIQUES_REQ,
    "06_santander_customer": SANTANDER_CUSTOMER_TRANSACTION_PREDICTION_REQ,
    "07_icr_identify": ICR_IDENTITY_AGE_RELATED_CONDITIONS_REQ,
    "08_santander_value": SANTANDER_VALUE_PREDICTION_CHALLENGE_REQ,
}

OPEN_ENDED_TASKS_REQUIREMENTS = {
    "01_ocr": OCR_REQ_01,
    "02_ocr": OCR_REQ_02,
    "03_ocr": OCR_REQ_03,
    "04_web_search_and_crawling": WEB_SEARCH_AND_CRAWLING_REQ_04,
    "05_web_search_and_crawling": WEB_SEARCH_AND_CRAWLING_REQ_05,
    "06_web_search_and_crawling": WEB_SEARCH_AND_CRAWLING_REQ_06,
    "07_web_search_and_crawling": WEB_SEARCH_AND_CRAWLING_REQ_07,
    "08_email_reply": EMAIL_REPLY_REQ_08,
    "09_web_page_imitation": WEB_PAGE_IMITATION_REQ_09,
    "10_web_page_imitation": WEB_PAGE_IMITATION_REQ_10,
    "11_web_page_imitation": WEB_PAGE_IMITATION_REQ_11,
    "12_web_page_imitation": WEB_PAGE_IMITATION_REQ_12,
    "13_web_page_imitation": WEB_PAGE_IMITATION_REQ_13,
    "14_image_background_removal": IMAGE_BACKGROUND_REMOVAL_REQ_14,
    "15_text2img": TEXT2IMG_REQ_15,
    "16_image_2_code_generation": IMAGE2CODE_GENERATION_REQ_16,
    "17_image_2_code_generation": IMAGE2CODE_GENERATION_REQ_17,
    "18_generate_games": GENERATE_GAMES_REQ_18,
    "19_generate_games": GENERATE_GAMES_REQ_19,
    "20_generate_games": GENERATE_GAMES_REQ_20,
}
