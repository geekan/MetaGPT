# -*- coding: utf-8 -*-
# @Date    :
# @Author  : 宏伟（散人）
# @Desc    :

import re


def replace_newlines(text):
    """
    将文本中的所有换行符('\n'、'\r\n')都替换为','

    Args:
        text (str): 输入文本

    Returns:
        str: 替换后的文本
    """
    return re.sub(r'[\r\n]+', ',', text)


def novel_filter_text(text):
    """
    从文本中过滤掉包含"第"、"章"、"上一"和"下一"这些字样的部分。

    Args:
        text (str): 输入文本

    Returns:
        str: 过滤后的文本
    """
    pattern = r'第\d+章|上一章|下一章|第.+?章'
    return re.sub(pattern, '', text)
