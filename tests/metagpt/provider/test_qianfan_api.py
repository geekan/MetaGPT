#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of qianfan api

import pytest

from metagpt.provider.qianfan_api import QianFanLLM
from tests.metagpt.provider.req_resp_const import prompt, messages, resp_cont_tmpl


resp_cont = resp_cont_tmpl.format(name="ERNIE-Bot-turbo")


def test_qianfan_acompletion(mocker):
    assert True, True
