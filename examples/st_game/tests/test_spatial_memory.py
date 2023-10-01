from ..utils.const import STORAGE_PATH
from ..memory.spatial_memory import MemoryTree

def test_spatial_memory():
    x = STORAGE_PATH.joinpath("base_the_ville_isabella_maria_klaus\personas\Isabella Rodriguez\bootstrap_memory\spatial_memory.json")
    x = MemoryTree(x)
    x.print_tree()