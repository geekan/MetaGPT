import unittest
import json5

from metagpt.utils.resp_parse import flatten_json_object

class TestFlattenJsonObject(unittest.TestCase):
    def test_flatten_json_object(self):
        json_obj = json5.loads('{"a": 1, "b": {"c": 2, "d": {"e": 3, "f": 4}}, "g": [5, 6, 7]}')
        expected_result = {'a': 1, 'b, c': 2, 'b, d, e': 3, 'b, d, f': 4, 'g': '5, 6, 7'}
        self.assertEqual(flatten_json_object(json_obj), expected_result)

    def test_flatten_json_object_with_string(self):
        json_obj = json5.loads('{"a": "hello"}')
        expected_result = {'a': 'hello'}
        self.assertEqual(flatten_json_object(json_obj), expected_result)

    def test_flatten_json_object_with_list(self):
        json_obj = json5.loads('{"a": [1, 2, 3]}')
        expected_result = {'a': '1, 2, 3'}
        self.assertEqual(flatten_json_object(json_obj), expected_result)

if __name__ == '__main__':
    unittest.main()
