from flask import Flask
from services.metagpt import runModel

app = Flask(__name__)


@app.get('/')
def health_check():
    return 'app running'


@app.get("/generate")
def generate():
    # get prompt from request
    runModel(prompt)
    # upload output
    # FileUploader.upload();
    return "<p\>Hello, World!</p>"

# create flask server
# call startup - fire.Fire(main)
# upload files to S3
# get files from workspace
# insert ids into db for current user
# return success or failed message
