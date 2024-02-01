## 命令行安装

### 支持的系统和版本
|     系统版本     | Python 版本     |  是否支持  |
|      ----      |     ----        |   -----   |
|   macOS 13.x   |    python 3.9   |    是    |
|   Windows 11   |    python 3.9   |    是    |
|   Ubuntu 22.04 |    python 3.9   |    是    |

### 详细安装

```bash
# 步骤 1: 确保您的系统安装了 Python 3.9 或更高版本。您可以使用以下命令来检查:
# 您可以使用 conda 来初始化一个新的 Python 环境
#     conda create -n metagpt python=3.9
#     conda activate metagpt
python3 --version

# 步骤 2: 克隆仓库到您的本地机器以获取最新版本，并安装它。
git clone https://github.com/geekan/MetaGPT.git
cd MetaGPT
pip3 install -e .     # 或 pip3 install metagpt  # 用于稳定版本

# 步骤 3: 在 config2.yaml 文件中设置您的 LLM 密钥
mkdir ~/.metagpt
cp config/config2.yaml ~/.metagpt/config2.yaml
vim ~/.metagpt/config2.yaml

# 步骤 4: 运行 metagpt 命令行界面
metagpt "用 python 创建一个 2048 游戏"

# 步骤 5 [可选]: 如果您想保存诸如象限图、系统设计、序列流等图表作为工作空间的工件，您可以在执行步骤 3 之前执行此步骤。默认情况下，该框架是兼容的，整个过程可以完全不执行此步骤而运行。
# 如果执行此步骤，请确保您的系统上安装了 NPM。然后安装 mermaid-js。（如果您的计算机中没有 npm，请访问 Node.js 官方网站 https://nodejs.org/ 安装 Node.js，然后您将在计算机中拥有 npm 工具。）
npm --version
sudo npm install -g @mermaid-js/mermaid-cli
```

**注意：**

- 如果已经安装了Chrome、Chromium或MS Edge，可以通过将环境变量`PUPPETEER_SKIP_CHROMIUM_DOWNLOAD`设置为`true`来跳过下载Chromium。

- 一些人在全局安装此工具时遇到问题。在本地安装是替代解决方案，

    ```bash
    npm install @mermaid-js/mermaid-cli
    ```

- 不要忘记在config.yml中为mmdc配置

    ```yml
    mermaid:
      puppeteer_config: "./config/puppeteer-config.json"
      path: "./node_modules/.bin/mmdc"
    ```

- 如果`pip install -e.`失败并显示错误`[Errno 13] Permission denied: '/usr/local/lib/python3.11/dist-packages/test-easy-install-13129.write-test'`，请尝试使用`pip install -e. --user`运行。
