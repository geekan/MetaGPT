#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

import pytest


def test_nodeid(request):
    print(request.node.nodeid)
    assert request.node.nodeid


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
