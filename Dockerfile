# This Dockerfile is friendly to users in Chinese Mainland :)
# For users outside mainland China, feel free to modify or delete them :)

# Use a base image with Python 3.9.17 slim version (Bullseye)
FROM nikolaik/python-nodejs:python3.9-nodejs20-slim

# Install Debian software needed by MetaGPT
RUN apt update &&\
    apt install -y git chromium fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 --no-install-recommends &&\
    apt clean

# Set the working directory to /app
WORKDIR /app

# Install Mermaid CLI globally 
ENV CHROME_BIN="/usr/bin/chromium"
ENV AM_I_IN_A_DOCKER_CONTAINER Yes
ADD puppeteer-config.json  /puppeteer-config.json
RUN npm install -g @mermaid-js/mermaid-cli &&\
    npm cache clean --force

# Copy src to container the MetaGPT repository
COPY . /app/metagpt

# Install Python dependencies and install MetaGPT
RUN cd metagpt &&\
    mkdir workspace &&\
    pip install -r requirements.txt &&\
    pip cache purge &&\
    python setup.py install

# Add metagpt user so we don't need --no-sandbox when use puppeteer
RUN useradd -m metagpt -s /bin/bash &&\
    chown metagpt -R /app/metagpt 

WORKDIR /app/metagpt
USER metagpt

# Running with an infinite loop using the tail command
CMD ["sh", "-c", "tail -f /dev/null"]