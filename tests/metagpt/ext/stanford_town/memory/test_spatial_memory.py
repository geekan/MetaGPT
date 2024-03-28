#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of MemoryTree

from metagpt.ext.stanford_town.memory.spatial_memory import MemoryTree
from metagpt.ext.stanford_town.utils.const import STORAGE_PATH


def test_spatial_memory():
    f_path = STORAGE_PATH.joinpath(
        "base_the_ville_isabella_maria_klaus/personas/Isabella Rodriguez/bootstrap_memory/spatial_memory.json"
    )
    x = MemoryTree()
    x.set_mem_path(f_path)
    assert x.tree
    assert "the Ville" in x.tree
    assert "Isabella Rodriguez's apartment" in x.get_str_accessible_sectors("the Ville")
