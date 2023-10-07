import unittest

from metagpt.utils.resp_parse import try_parse_json


class TestTryParseJson(unittest.TestCase):
    def test_valid_json(self):
        input_text = '{"name": "John", "age": 30, "city": "New York"}'
        expected_output = {"name": "John", "age": 30, "city": "New York"}
        self.assertEqual(try_parse_json(input_text), expected_output)

    def test_invalid_json(self):
        input_text = 'This is not a JSON string'
        with self.assertRaises(Exception) as context:
            try_parse_json(input_text)
        self.assertTrue('No JSON object found in input text.' in str(context.exception))

    def test_empty_json(self):
        input_text = '{}'
        expected_output = {}
        self.assertEqual(try_parse_json(input_text), expected_output)

    def test_nested_json(self):
        input_text = '{"name": "John", "age": 30, "city": "New York", "friends": ["Mike", "Anna"]}'
        expected_output = {"name": "John", "age": 30, "city": "New York", "friends": ["Mike", "Anna"]}
        self.assertEqual(try_parse_json(input_text), expected_output)

if __name__ == '__main__':
    unittest.main()
    try_parse_json('{"a": [ jjj}')