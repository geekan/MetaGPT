import unittest

from metagpt.utils.resp_parse import flatten_json_structure

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
