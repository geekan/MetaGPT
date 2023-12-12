#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/10 20:12
# @Author  : lidanyang
# @File    : base
# @Desc    :
class MLProcess(object):
    def fit(self, df):
        raise NotImplementedError

    def transform(self, df):
        raise NotImplementedError

    def fit_transform(self, df):
        self.fit(df)
        return self.transform(df)
