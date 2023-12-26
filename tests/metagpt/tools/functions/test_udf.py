import pytest
import yaml
import json

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


def test_UDFS_YAML():
    assert len(UDFS_YAML) > 0
    logger.info(f"\n\n{json.dumps(UDFS_YAML, indent=2, ensure_ascii=False)}")
    function_schema = UDFS_YAML
    assert 'description' in function_schema[list(function_schema.keys())[0]]
    assert 'type' in function_schema[list(function_schema.keys())[0]]
    assert 'parameters' in function_schema[list(function_schema.keys())[0]]
    assert 'properties' in function_schema[list(function_schema.keys())[0]]['parameters']
    assert 'required' in function_schema[list(function_schema.keys())[0]]['parameters']
    assert 'returns' in function_schema[list(function_schema.keys())[0]]
    # 指定要保存的文件路径
    file_path = './tests/data/function_schema.yaml'

    # 使用 PyYAML 将字典保存为 YAML 文件
    with open(file_path, 'w') as file:
        yaml.dump(function_schema, file, default_flow_style=False)

    print(f'Data has been saved to {file_path}')
