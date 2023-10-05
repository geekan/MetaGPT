from ..utils.const import STORAGE_PATH
from ..memory.spatial_memory import MemoryTree

def test_spatial_memory():
    f_path = STORAGE_PATH.joinpath("base_the_ville_isabella_maria_klaus/personas/Isabella Rodriguez/bootstrap_memory/spatial_memory.json")
    x = MemoryTree(f_path)
    assert x.tree
    assert "the Ville" in x.tree
    assert "Isabella Rodriguez's apartment" in x.get_str_accessible_sectors("the Ville")