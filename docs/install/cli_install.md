## Traditional Command Line Installation

### Support System and version
| System Version | Python Version  |  Supported  |
|      ----      |     ----        |   -----   |
|   macOS 13.x   |    python 3.9   |    Yes    |
|   Windows 11   |    python 3.9   |    Yes    |
|   Ubuntu 22.04 |    python 3.9   |    Yes    |

### Detail Installation
```bash
# Step 1: Ensure that Python 3.9+ is installed on your system. You can check this by using:
# You can use conda to initialize a new python env
#     conda create -n metagpt python=3.9
#     conda activate metagpt
python3 --version

# Step 2: Clone the repository to your local machine for latest version, and install it.
git clone https://github.com/geekan/MetaGPT.git
cd MetaGPT
pip3 install -e .     # or pip3 install metagpt  # for stable version

# Step 3: setup your LLM key in the config2.yaml file
mkdir ~/.metagpt
cp config/config2.yaml ~/.metagpt/config2.yaml
vim ~/.metagpt/config2.yaml

# Step 4: run metagpt cli
metagpt "Create a 2048 game in python"

# Step 5 [Optional]: If you want to save the artifacts like diagrams such as quadrant chart, system designs, sequence flow in the workspace, you can execute the step before Step 3. By default, the framework is compatible, and the entire process can be run completely without executing this step.
# If executing, ensure that NPM is installed on your system. Then install mermaid-js. (If you don't have npm in your computer, please go to the Node.js official website to install Node.js https://nodejs.org/ and then you will have npm tool in your computer.)
npm --version
sudo npm install -g @mermaid-js/mermaid-cli
```

**Note:**

- If already have Chrome, Chromium, or MS Edge installed, you can skip downloading Chromium by setting the environment variable
  `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD` to `true`.

- Some people are [having issues](https://github.com/mermaidjs/mermaid.cli/issues/15) installing this tool globally. Installing it locally is an alternative solution,

  ```bash
  npm install @mermaid-js/mermaid-cli
  ```

- don't forget to the configuration for mmdc path in config.yml

  ```yaml
  mermaid:
    puppeteer_config: "./config/puppeteer-config.json"
    path: "./node_modules/.bin/mmdc"
  ```

- if `pip install -e.` fails with error `[Errno 13] Permission denied: '/usr/local/lib/python3.11/dist-packages/test-easy-install-13129.write-test'`, try instead running `pip install -e. --user`

- To convert Mermaid charts to SVG, PNG, and PDF formats. In addition to the Node.js version of Mermaid-CLI, you now have the option to use Python version Playwright, pyppeteer or mermaid.ink for this task.

  - Playwright
    - **Install Playwright**

    ```bash
    pip install playwright
    ```

    - **Install the Required Browsers**

    to support PDF conversion, please install Chrominum.

    ```bash
    playwright install --with-deps chromium
    ```

    - **modify `config2.yaml`**

    change mermaid.engine to `playwright`

    ```yaml
    mermaid:
      engine: playwright
    ```

  - pyppeteer
    - **Install pyppeteer**

    ```bash
    pip install pyppeteer
    ```

    - **Use your own Browsers**

    pyppeteer allows you use installed browsers,  please set the following envirment
    
    ```bash
    export PUPPETEER_EXECUTABLE_PATH = /path/to/your/chromium or edge or chrome
    ```

    please do not use this command to install browser, it is too old

    ```bash
    pyppeteer-install
    ```

    - **modify `config2.yaml`**

    change mermaid.engine to `pyppeteer`

    ```yaml
    mermaid:
      engine: pyppeteer
    ```

  - mermaid.ink
    - **modify `config2.yaml`**
    
    change mermaid.engine to `ink`

    ```yaml
    mermaid:
      engine: ink
    ```  

    Note: this method does not support pdf export.
    
