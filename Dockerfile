# This Dockerfile is friendly to users in Chinese Mainland :)
# For users outside mainland China, feel free to modify or delete them :)

# Use a base image with Python 3.9.17 slim version (Bullseye)
FROM python:3.9.17-slim-bullseye

# Install Debian software needed by MetaGPT
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list &&\
    apt update &&\
    apt install -y git curl wget build-essential gcc clang g++ make gnupg &&\
    curl -sL https://deb.nodesource.com/setup_19.x | bash - &&\
    apt install -y nodejs &&\
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - &&\
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' &&\
    apt-get update &&\
    apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 --no-install-recommends &&\
    apt-get clean

# Set the working directory to /app
WORKDIR /app

# Install Mermaid CLI globally and clone the MetaGPT repository
#ENV PUPPETEER_SKIP_DOWNLOAD='true'
RUN npm config set registry https://registry.npm.taobao.org &&\
    npm install -g @mermaid-js/mermaid-cli &&\
    npm cache clean --force &&\
    git clone https://github.com/geekan/metagpt

# Install Python dependencies and install MetaGPT
RUN cd metagpt &&\
    mkdir workspace &&\
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ &&\
    pip install -r requirements.txt &&\
    pip cache purge &&\
    python setup.py install

# Add metagpt user so we don't need --no-sandbox when use puppeteer
RUN useradd -m metagpt -s /bin/bash &&\
    chown metagpt -R /app/metagpt &&\
    cp -r /root/.cache /home/metagpt/ &&\
    chown metagpt -R /home/metagpt/.cache &&\
    chrome_sandbox=$(find /root/.cache/puppeteer/chrome/ -name "chrome_sandbox") &&\
    cp $chrome_sandbox /usr/local/sbin/chrome-devel-sandbox &&\
    chmod 4755 /usr/local/sbin/chrome-devel-sandbox

ENV CHROME_DEVEL_SANDBOX=/usr/local/sbin/chrome-devel-sandbox

WORKDIR /app/metagpt
USER metagpt

# Running with an infinite loop using the tail command
CMD ["sh", "-c", "tail -f /dev/null"]