#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2025/2/10 18:40:40
@Author  : terrdi
@File    : format.py
@Describe : llm response format field definition
"""

from abc import abstractmethod
from pydantic import BaseModel, Field
from metagpt.configs.llm_config import LLMType
from metagpt.logs import logger
import json

class ResponseFormat(BaseModel):
    """
    llm response format field definition
    """
    @abstractmethod
    def get_response_format(self, llm_type: LLMType):
        """
        Convert the ResponseFormat object to a JSON string.
        """
        raise NotImplementedError
    
    """
    llm response format with custom key
    """
    @abstractmethod
    def get_response_format(self, custom_key: str):
        """
        Convert the ResponseFormat object to a JSON string.
        """
        raise NotImplementedError
    
    @abstractmethod
    def add_property(self, key: str, describe: str, type: str, required: bool = False):
        """
        Add a property to the ResponseFormat object.
        """
        raise NotImplementedError
    
    @abstractmethod
    def remove_property(self, key: str):
        """
        Remove a property from the ResponseFormat object.
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_property_type(self, key: str) -> type:
        """
        Get the type of a property.
        """
        raise NotImplementedError
    


    def get_most_likely_key(self, json_dict: dict[str, any], target_key: str, default: any = None) -> any:
        """
        Get the most likely key from a dictionary based on the edit distance.
        """
        min_distance = float('inf')
        min_key = None
        str_lower = target_key.lower()
        for key in json_dict.keys():
            distance = minest_edit_distance(key.lower(), str_lower)
            if distance < min_distance:
                min_distance = distance
                min_key = key
        ret = json_dict[min_key] if min_key else default
        target_type = self.get_property_type(target_key) if min_key else None
        if ret is None or isinstance(ret, target_type):
            return ret
        elif isinstance(ret, dict):
            return self.get_most_likely_key(ret, target_key, default)
        else:
            return default
    

class JsonResponseFormat(ResponseFormat):
    """
    llm response format field definition
    """
    properties_describe: dict[str, str] = Field(default_factory=dict)
    properties_type: dict[str, str] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additionalProperties: bool = True

    def to_json(self):
        """
        Convert the ResponseFormat object to a JSON string.
        """
        return self.model_dump_json()
    
    def to_dict(self):
        """
        Convert the ResponseFormat object to a dictionary.
        """
        ret = self.model_dump()
        ret["properties"] = {}
        for key, value in self.properties_describe.items():
            ret["properties"][key] = {
                "type": self.properties_type[key],
                "description": value,
            }
        del ret["properties_describe"]
        del ret["properties_type"]
        return ret
    
    def add_property(self, key: str, describe: str, type: str, required: bool = False):
        """
        Add a property to the ResponseFormat object.
        """
        self.properties_describe[key] = describe
        self.properties_type[key] = type
        if required:
            self.required.append(key)
    
    def remove_property(self, key: str):
        """
        Remove a property from the ResponseFormat object.
        """
        if key in self.properties_describe:
            del self.properties_describe[key]
        if key in self.required:
            self.required.remove(key)
        if key in self.properties_type:
            del self.properties_type[key]
    

    @property
    def llm_type_functions(self):
        ret = self.to_dict()
        return {
            LLMType.OPENAI.value: ret | {"type": "json_object"},
            LLMType.LLMSTUDIO.value: {
                "type": "json_schema",
                "json_schema": {
                    "schema": ret | {"type": "object"},
                },
            },
            LLMType.OLLAMA.value: json.dumps(ret | {"type": "object"}),
            # use just 'json' for ollama version less than 0.5.0
            'ollama_low_version': 'json'
        }


    def get_response_format(self, llm_type: LLMType):
        """
        Convert the ResponseFormat object to a JSON string.
        """
        try:
            return self.get_response_format_with_custom_key(llm_type.value)
        except KeyError:
            logger.warning(f"Unsupported LLM type: {llm_type}, using default json_object")
            return self.to_dict() | {"type": "object"}
        
    def get_response_format_with_custom_key(self, custom_key: str):
        """
        Convert the ResponseFormat object to a JSON string.
        """
        return self.llm_type_functions[custom_key]

    def get_property_type(self, key: str) -> type:
        """
        Get the type of a property.
        """
        return get_type_from_str(self.properties_type[key])


    def update_describe_with_dict(self, describe_dict: dict[str, str]):
        """
        Update the describe of the ResponseFormat object with a dictionary.
        """
        for key, value in self.properties_describe.items():
            for k, v in describe_dict.items():
                if k in value:
                    self.properties_describe[key] = value.replace(k, v)
    


def minest_edit_distance(str1: str, str2: str) -> int:
    """
    Calculate the minimum edit distance between two strings.
    """
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1
    return dp[m][n] 


def get_type_from_str(str_value: str) -> str:
    """
    Get the type from a string.
    """
    if str_value.lower().startswith("bool"):
        return bool
    elif str_value.lower().startswith("int"):
        return int
    elif str_value.lower().startswith("float"):
        return float
    elif str_value.lower().startswith("str"):
        return str
    elif str_value.lower().startswith("list") or str_value.lower().startswith("array"):
        return list
    else:
        return dict

