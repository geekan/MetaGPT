## Traditional Command Line Installation

### Support System and version
| System Version | Python Version  |  Supported  |
|      ----      |     ----        |   -----   |
|   macOS 13.x   |    python 3.9   |    Yes    |
|   Windows 11   |    python 3.9   |    Yes    |
|   Ubuntu 22.04 |    python 3.9   |    Yes    |

### Detail Installation
```bash
# Step 1: Ensure that NPM is installed on your system. Then install mermaid-js. (If you don't have npm in your computer, please go to the Node.js official website to install Node.js https://nodejs.org/ and then you will have npm tool in your computer.)
npm --version
sudo npm install -g @mermaid-js/mermaid-cli

# Step 2: Ensure that Python 3.9+ is installed on your system. You can check this by using:
python3 --version

# Step 3: Clone the repository to your local machine, and install it.
git clone https://github.com/geekan/MetaGPT.git
cd MetaGPT
pip install -e.
```

**Note:**

- If already have Chrome, Chromium, or MS Edge installed, you can skip downloading Chromium by setting the environment variable
  `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD` to `true`.

- Some people are [having issues](https://github.com/mermaidjs/mermaid.cli/issues/15) installing this tool globally. Installing it locally is an alternative solution,

  ```bash
  npm install @mermaid-js/mermaid-cli
  ```

- don't forget to the configuration for mmdc in config.yml

  ```yml
  PUPPETEER_CONFIG: "./config/puppeteer-config.json"
  MMDC: "./node_modules/.bin/mmdc"
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

    - **modify `config.yaml`**

    uncomment MERMAID_ENGINE from config.yaml and change it to `playwright`

    ```yaml
    MERMAID_ENGINE: playwright
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

    - **modify `config.yaml`**

    uncomment MERMAID_ENGINE from config.yaml and change it to `pyppeteer`

    ```yaml
    MERMAID_ENGINE: pyppeteer
    ```

  - mermaid.ink
    - **modify `config.yaml`**

    uncomment MERMAID_ENGINE from config.yaml and change it to `ink`

    ```yaml
    MERMAID_ENGINE: ink
    ```  

    Note: this method does not support pdf export.
    