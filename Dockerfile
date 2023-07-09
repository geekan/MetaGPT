FROM python:3.9.17-slim-bullseye

#Special gifts for mainland China users :) 
#Change to your own preferenced mirrors if you wish, just uncomment them is fine too.
    #Below is apt mirror setup.
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list &&\
    apt update &&\ 
    apt install -y git curl wget build-essential gcc clang g++ make &&\
    curl -sL https://deb.nodesource.com/setup_19.x | bash - &&\
    apt install -y nodejs 

    
WORKDIR /app
    #This sets npm mirror url.
RUN npm config set registry https://registry.npm.taobao.org &&\
    npm install -g @mermaid-js/mermaid-cli &&\
    git clone https://github.com/geekan/metagpt
RUN cd metagpt &&\
    mkdir workspace &&\
    #This sets the pip mirror url.
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ &&\
    pip install -r requirements.txt --no-cache-dir &&\
    python setup.py install

RUN pip cache purge &&\
    apt autoclean


