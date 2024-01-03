from pathlib import Path
from pprint import pformat

from metagpt.const import METAGPT_ROOT
from metagpt.logs import logger
from metagpt.repo_parser import RepoParser


def test_repo_parser():
    repo_parser = RepoParser(base_directory=METAGPT_ROOT / "metagpt" / "strategy")
    symbols = repo_parser.generate_symbols()
    logger.info(pformat(symbols))

    assert "tot_schema.py" in str(symbols)

    output_path = repo_parser.generate_structure(mode="json")
    assert output_path.exists()
    output_path = repo_parser.generate_structure(mode="csv")
    assert output_path.exists()


def test_error():
    """_parse_file should return empty list when file not existed"""
    rsp = RepoParser._parse_file(Path("test_not_existed_file.py"))
    assert rsp == []
