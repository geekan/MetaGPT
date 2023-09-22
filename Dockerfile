# Use a base image with Python3.9 and Nodejs20 slim version
FROM nikolaik/python-nodejs:python3.10-nodejs20-slim
WORKDIR /app/metagpt
# Install Debian software needed by MetaGPT and clean up in one RUN command to reduce image size
RUN apt update &&\
    apt install -y git chromium fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 --no-install-recommends &&\
    apt clean && rm -rf /var/lib/apt/lists/*

# Install Mermaid CLI globally
ENV CHROME_BIN="/usr/bin/chromium" \
    PUPPETEER_CONFIG="/app/metagpt/config/puppeteer-config.json"\
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true"
RUN npm install -g @mermaid-js/mermaid-cli &&\
    npm cache clean --force

#Install poetry
RUN pip install poetry

#copy only requirements to cache them in an earlier layer
COPY poetry.lock pyproject.toml  /app/metagpt/

#attempt to turn off venv creation
RUN poetry config virtualenvs.create false

#in case there is a .venv folder for some reason.
RUN rm -rf .venv

# Install project dependencies only
RUN poetry install --no-interaction --no-ansi --all-extras

#copy project files
COPY . .

RUN mkdir workspace

#Install references to package itself to resolve imports
RUN poetry install

# Running with an infinite loop using the tail command
CMD ["sh", "-c", "tail -f /dev/null"]

