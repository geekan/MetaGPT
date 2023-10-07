# -*- coding: utf-8 -*-
# @Date    : 2023/10/7 16:32
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

import yaml

from metagpt.const import PROJECT_ROOT


def load_extra_conf(yaml_file=PROJECT_ROOT / "config/add_config.yaml"):
    with open(yaml_file, "r", encoding="utf-8") as file:
        yaml_data = yaml.safe_load(file)
        
        return yaml_data
