import pytest

from metagpt.actions.di.detect_intent import DetectIntent
from metagpt.schema import Message

SOFTWARE_DEV_REQ1 = """
I'd like to create a personalized website that features the 'Game of Life' simulation.
"""

SOFTWARE_DEV_REQ2 = """
Create a website widget for TODO list management.
"""

SOFTWARE_DEV_REQ3 = """
Create an official website with a top bar, banner, About Us section, and footer.
"""

DI_REQ1 = """
can you finetune a 78 Llama model using https://github.com/huggingface/peft should be instructions in the Readme.
"""

DI_REQ2 = """
I came across a blog post on the website Mafengwo (https://www.mafengwo.cn/i/17171539.html) that discusses the possibility of generating images with hidden text. The post refers to a script that can be used for this purpose. Could you help me set up this script and use it to generate some images? I would like the images to have the hidden text 'MAX' and also some with 'MetaGPT' as the hidden text.
"""

DI_REQ3 = """
Extract all of the blog posts from `https://stripe.com/blog/page/1` and return a CSV with the columns `date`, `article_text`, `author` and `summary`. Generate a summary for each article yourself.
"""

FIX_BUG_REQ = """
Fix this error from the 2048 game repo: TypeError: __init__() takes 1 positional argument but 2 were given"
"""

FORMAT_REPO_REQ = """
git clone 'https://github.com/spec-first/connexion' and format to MetaGPT project
"""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "requirement, expected_intent_type",
    [
        (SOFTWARE_DEV_REQ1, "software development"),
        (SOFTWARE_DEV_REQ2, "software development"),
        (SOFTWARE_DEV_REQ3, "software development"),
        (DI_REQ1, "other"),
        (DI_REQ2, "other"),
        (DI_REQ3, "other"),
        (FIX_BUG_REQ, "fix bugs"),
        (FORMAT_REPO_REQ, "format repo"),
    ],
)
async def test_detect_intent(requirement, expected_intent_type):
    di = DetectIntent()
    _, intent_type = await di.run([Message(role="user", content=requirement)])
    assert intent_type == expected_intent_type
