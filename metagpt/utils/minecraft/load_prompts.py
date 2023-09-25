# -*- coding: utf-8 -*-
# @Date    : 2023/9/24 11:03
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pkg_resources
from .file_utils import load_text
        
def load_prompt(prompt):
    package_path = pkg_resources.resource_filename("metagpt", "")
    return load_text(f"{package_path}/prompts/minecraft/{prompt}.txt")