import unittest
import json5
import re


def flatten_json_object(obj, parent_key='', sep=', '):
    if isinstance(obj, str):
        return dict([("value", obj)])
    
    if isinstance(obj, list):
        return dict([("value", sep.join(str(v) for v in obj))])
    
    items = []
    for key, value in obj.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_json_object(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            items.append((new_key, sep.join(str(v) for v in value)))
        else:
            items.append((new_key, value))
    return dict(items)

def flatten_json_structure(json_array):
    if (isinstance(json_array, list) and len(json_array) == 1 and not isinstance(json_array[0], str)):
        return flatten_json_structure(json_array[0])
    
    if (isinstance(json_array, dict) and len(json_array.values()) == 1 and not isinstance(list(json_array.values())[0],
                                                                                          str)):
        return flatten_json_structure(list(json_array.values())[0])
    
    flattened_json_array = []
    
    if (isinstance(json_array, dict)):
        json_array = json_array.values()
    
    for json_object in json_array:
        flattened_dict = flatten_json_object(json_object)
        flattened_values = ", ".join(str(v) for v in flattened_dict.values())
        flattened_json_array.append(flattened_values)
    
    return flattened_json_array

class TestFlattenJson(unittest.TestCase):
    def test_flatten_json_structure(self):
        input_json = [
            {
                "name": "John",
                "age": 30,
                "city": "New York"
            },
            {
                "name": "Jane",
                "age": 25,
                "city": "Chicago"
            }
        ]
        expected_output = ["John, 30, New York", "Jane, 25, Chicago"]
        self.assertEqual(flatten_json_structure(input_json), expected_output)

    def test_flatten_json_structure_with_nested_json(self):
        input_json = [
            {
                "name": "John",
                "age": 30,
                "address": {
                    "city": "New York",
                    "state": "NY"
                }
            },
            {
                "name": "Jane",
                "age": 25,
                "address": {
                    "city": "Chicago",
                    "state": "IL"
                }
            }
        ]
        expected_output = ["John, 30, New York, NY", "Jane, 25, Chicago, IL"]
        self.assertEqual(flatten_json_structure(input_json), expected_output)

if __name__ == '__main__':
    unittest.main()
