import pytest
import yaml

from metagpt.tools.functions.libs.udf import UDFS, docstring_to_yaml, UDFS_YAML
from metagpt.logs import logger


def test_udfs():
    assert len(UDFS) > 0
    assert 'udf_name' in UDFS[0]
    assert 'udf_doc' in UDFS[0]
    logger.info(UDFS)


def test_docstring2yaml():
    docstring = """Calculate the duration in hours between two datetime columns.

    Args:
        dataframe (pd.DataFrame): The dataframe containing the datetime columns.

    Returns:
        pd.DataFrame: The dataframe with an additional column 'duration_hour' added.
    """

    yaml_result = docstring_to_yaml(docstring, return_vars='dataframe')
    assert 'parameters' in yaml_result
    assert 'properties' in yaml_result['parameters']
    assert 'dataframe' in yaml_result['parameters']['properties']


def test_docstring2yaml_error():
    docstring = """Calculate the duration in hours between two datetime columns.
    args:
        dataframe (pd.DataFrame): The dataframe containing the datetime columns.
    returns:
        pd.DataFrame: The dataframe with an additional column 'duration_hour' added.
    """
    with pytest.raises(ValueError) as exc_info:
        docstring_to_yaml(docstring, return_vars='dataframe')
        assert "No Args found" in exc_info


def test_UDFS_YAML():
    assert len(UDFS_YAML) > 0
    logger.info(f"\n\n{UDFS_YAML}")
    function_schema = yaml.load(UDFS_YAML, Loader=yaml.FullLoader)
    assert 'description' in function_schema[list(function_schema.keys())[0]]
    assert 'type' in function_schema[list(function_schema.keys())[0]]
    assert 'parameters' in function_schema[list(function_schema.keys())[0]]
    assert 'properties' in function_schema[list(function_schema.keys())[0]]['parameters']
    assert 'required' in function_schema[list(function_schema.keys())[0]]['parameters']
    assert 'returns' in function_schema[list(function_schema.keys())[0]]
