from pathlib import Path
from pprint import pformat

import pytest

from metagpt.const import METAGPT_ROOT
from metagpt.logs import logger
from metagpt.repo_parser import DotClassAttribute, DotClassMethod, DotReturn, RepoParser


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


@pytest.mark.parametrize(
    ("v", "name", "type_", "default_", "compositions"),
    [
        ("children : dict[str, 'ActionNode']", "children", "dict[str,ActionNode]", "", ["ActionNode"]),
        ("context : str", "context", "str", "", []),
        ("example", "example", "", "", []),
        ("expected_type : Type", "expected_type", "Type", "", ["Type"]),
        ("args : Optional[Dict]", "args", "Optional[Dict]", "", []),
        ("rsp : Optional[Message] = Message.Default", "rsp", "Optional[Message]", "Message.Default", ["Message"]),
        (
            "browser : Literal['chrome', 'firefox', 'edge', 'ie']",
            "browser",
            "Literal['chrome','firefox','edge','ie']",
            "",
            [],
        ),
        (
            "browser : Dict[ Message, Literal['chrome', 'firefox', 'edge', 'ie'] ]",
            "browser",
            "Dict[Message,Literal['chrome','firefox','edge','ie']]",
            "",
            ["Message"],
        ),
        ("attributes : List[ClassAttribute]", "attributes", "List[ClassAttribute]", "", ["ClassAttribute"]),
        ("attributes = []", "attributes", "", "[]", []),
        (
            "request_timeout: Optional[Union[float, Tuple[float, float]]]",
            "request_timeout",
            "Optional[Union[float,Tuple[float,float]]]",
            "",
            [],
        ),
    ],
)
def test_parse_member(v, name, type_, default_, compositions):
    attr = DotClassAttribute.parse(v)
    assert name == attr.name
    assert type_ == attr.type_
    assert default_ == attr.default_
    assert compositions == attr.compositions
    assert v == attr.description

    json_data = attr.model_dump_json()
    v = DotClassAttribute.model_validate_json(json_data)
    assert v == attr


@pytest.mark.parametrize(
    ("line", "package_name", "info"),
    [
        (
            '"metagpt.roles.architect.Architect" [color="black", fontcolor="black", label=<{Architect|constraints : str<br ALIGN="LEFT"/>goal : str<br ALIGN="LEFT"/>name : str<br ALIGN="LEFT"/>profile : str<br ALIGN="LEFT"/>|}>, shape="record", style="solid"];',
            "metagpt.roles.architect.Architect",
            "Architect|constraints : str\ngoal : str\nname : str\nprofile : str\n|",
        ),
        (
            '"metagpt.actions.skill_action.ArgumentsParingAction" [color="black", fontcolor="black", label=<{ArgumentsParingAction|args : Optional[Dict]<br ALIGN="LEFT"/>ask : str<br ALIGN="LEFT"/>prompt<br ALIGN="LEFT"/>rsp : Optional[Message]<br ALIGN="LEFT"/>skill<br ALIGN="LEFT"/>|parse_arguments(skill_name, txt): dict<br ALIGN="LEFT"/>run(with_message): Message<br ALIGN="LEFT"/>}>, shape="record", style="solid"];',
            "metagpt.actions.skill_action.ArgumentsParingAction",
            "ArgumentsParingAction|args : Optional[Dict]\nask : str\nprompt\nrsp : Optional[Message]\nskill\n|parse_arguments(skill_name, txt): dict\nrun(with_message): Message\n",
        ),
        (
            '"metagpt.strategy.base.BaseEvaluator" [color="black", fontcolor="black", label=<{BaseEvaluator|<br ALIGN="LEFT"/>|<I>status_verify</I>()<br ALIGN="LEFT"/>}>, shape="record", style="solid"];',
            "metagpt.strategy.base.BaseEvaluator",
            "BaseEvaluator|\n|<I>status_verify</I>()\n",
        ),
        (
            '"metagpt.configs.browser_config.BrowserConfig" [color="black", fontcolor="black", label=<{BrowserConfig|browser : Literal[\'chrome\', \'firefox\', \'edge\', \'ie\']<br ALIGN="LEFT"/>driver : Literal[\'chromium\', \'firefox\', \'webkit\']<br ALIGN="LEFT"/>engine<br ALIGN="LEFT"/>path : str<br ALIGN="LEFT"/>|}>, shape="record", style="solid"];',
            "metagpt.configs.browser_config.BrowserConfig",
            "BrowserConfig|browser : Literal['chrome', 'firefox', 'edge', 'ie']\ndriver : Literal['chromium', 'firefox', 'webkit']\nengine\npath : str\n|",
        ),
        (
            '"metagpt.tools.search_engine_serpapi.SerpAPIWrapper" [color="black", fontcolor="black", label=<{SerpAPIWrapper|aiosession : Optional[aiohttp.ClientSession]<br ALIGN="LEFT"/>model_config<br ALIGN="LEFT"/>params : dict<br ALIGN="LEFT"/>search_engine : Optional[Any]<br ALIGN="LEFT"/>serpapi_api_key : Optional[str]<br ALIGN="LEFT"/>|check_serpapi_api_key(val: str)<br ALIGN="LEFT"/>get_params(query: str): Dict[str, str]<br ALIGN="LEFT"/>results(query: str, max_results: int): dict<br ALIGN="LEFT"/>run(query, max_results: int, as_string: bool): str<br ALIGN="LEFT"/>}>, shape="record", style="solid"];',
            "metagpt.tools.search_engine_serpapi.SerpAPIWrapper",
            "SerpAPIWrapper|aiosession : Optional[aiohttp.ClientSession]\nmodel_config\nparams : dict\nsearch_engine : Optional[Any]\nserpapi_api_key : Optional[str]\n|check_serpapi_api_key(val: str)\nget_params(query: str): Dict[str, str]\nresults(query: str, max_results: int): dict\nrun(query, max_results: int, as_string: bool): str\n",
        ),
    ],
)
def test_split_class_line(line, package_name, info):
    p, i = RepoParser._split_class_line(line)
    assert p == package_name
    assert i == info


@pytest.mark.parametrize(
    ("v", "name", "args", "return_args"),
    [
        (
            "<I>arequest</I>(method, url, params, headers, files, stream: Literal[True], request_id: Optional[str], request_timeout: Optional[Union[float, Tuple[float, float]]]): Tuple[AsyncGenerator[OpenAIResponse, None], bool, str]",
            "arequest",
            [
                DotClassAttribute(name="method", description="method"),
                DotClassAttribute(name="url", description="url"),
                DotClassAttribute(name="params", description="params"),
                DotClassAttribute(name="headers", description="headers"),
                DotClassAttribute(name="files", description="files"),
                DotClassAttribute(name="stream", type_="Literal[True]", description="stream: Literal[True]"),
                DotClassAttribute(name="request_id", type_="Optional[str]", description="request_id: Optional[str]"),
                DotClassAttribute(
                    name="request_timeout",
                    type_="Optional[Union[float,Tuple[float,float]]]",
                    description="request_timeout: Optional[Union[float, Tuple[float, float]]]",
                ),
            ],
            DotReturn(
                type_="Tuple[AsyncGenerator[OpenAIResponse,None],bool,str]",
                compositions=["AsyncGenerator", "OpenAIResponse"],
                description="Tuple[AsyncGenerator[OpenAIResponse, None], bool, str]",
            ),
        ),
        (
            "<I>update</I>(subject: str, predicate: str, object_: str)",
            "update",
            [
                DotClassAttribute(name="subject", type_="str", description="subject: str"),
                DotClassAttribute(name="predicate", type_="str", description="predicate: str"),
                DotClassAttribute(name="object_", type_="str", description="object_: str"),
            ],
            DotReturn(description=""),
        ),
    ],
)
def test_parse_method(v, name, args, return_args):
    method = DotClassMethod.parse(v)
    assert method.name == name
    assert method.args == args
    assert method.return_args == return_args
    assert method.description == v

    json_data = method.model_dump_json()
    v = DotClassMethod.model_validate_json(json_data)
    assert v == method


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
