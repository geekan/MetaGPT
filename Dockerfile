# This Dockerfile is friendly to users in Chinese Mainland :) 
# For users outside mainland China, feel free to modify or delete them :)

# Use a base image with Python 3.9.17 slim version (Bullseye)
FROM python:3.9.17-slim-bullseye

# Install Debian software needed by MetaGPT
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list &&\
    apt update &&\
    apt install -y git curl wget build-essential gcc clang g++ make &&\
    curl -sL https://deb.nodesource.com/setup_19.x | bash - &&\
    apt install -y nodejs &&\
    apt-get clean

# Set the working directory to /app
WORKDIR /app

# Install Mermaid CLI globally and clone the MetaGPT repository
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

# Running with an infinite loop using the tail command
CMD ["sh", "-c", "tail -f /dev/null"]

