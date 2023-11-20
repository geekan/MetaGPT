## 命令行安装

### 支持的系统和版本
|     系统版本     | Python 版本     |  是否支持  |
|      ----      |     ----        |   -----   |
|   macOS 13.x   |    python 3.9   |    是    |
|   Windows 11   |    python 3.9   |    是    |
|   Ubuntu 22.04 |    python 3.9   |    是    |

### 详细安装

```bash
# 第 1 步：确保您的系统上安装了 NPM。并使用npm安装mermaid-js
npm --version
sudo npm install -g @mermaid-js/mermaid-cli

# 第 2 步：确保您的系统上安装了 Python 3.9+。您可以使用以下命令进行检查：
python --version

# 第 3 步：克隆仓库到您的本地机器，并进行安装。
git clone https://github.com/geekan/MetaGPT.git
cd MetaGPT
pip install -e.
```

**注意：**

- 如果已经安装了Chrome、Chromium或MS Edge，可以通过将环境变量`PUPPETEER_SKIP_CHROMIUM_DOWNLOAD`设置为`true`来跳过下载Chromium。

- 一些人在全局安装此工具时遇到问题。在本地安装是替代解决方案，

    ```bash
    npm install @mermaid-js/mermaid-cli
    ```

- 不要忘记在config.yml中为mmdc配置配置，

    ```yml
    PUPPETEER_CONFIG: "./config/puppeteer-config.json"
    MMDC: "./node_modules/.bin/mmdc"
    ```

- 如果`pip install -e.`失败并显示错误`[Errno 13] Permission denied: '/usr/local/lib/python3.11/dist-packages/test-easy-install-13129.write-test'`，请尝试使用`pip install -e. --user`运行。
