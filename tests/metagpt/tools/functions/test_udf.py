from metagpt.tools.functions.libs.udf import UDFS
from metagpt.logs import logger


def test_udfs():
    assert len(UDFS) > 0
    assert 'name' in UDFS[0]
    assert 'doc' in UDFS[0]
    logger.info(UDFS)
