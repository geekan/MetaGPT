import unittest
import json5
import re

def try_parse_json(input_text):
    input_text.index
    start_index_brackets = input_text.find('[')
    end_index_brackets = input_text.rfind(']')
    start_index_curly = input_text.find('{')
    end_index_curly = input_text.rfind('}')
    
    start_index = start_index_brackets
    end_index = end_index_brackets
    
    if (start_index_curly != -1 and (start_index_curly < start_index_brackets or start_index_brackets < 0)):
        start_index = start_index_curly
        end_index = end_index_curly
    
    if start_index >= 0 and end_index > 0:
        json_string = input_text[start_index:end_index + 1]
        json_string = re.sub(r'\}[\s]*\{', '}, {', json_string)
        json_string = re.sub(r'\][\s]*\[', '], [', json_string)
        json_string = re.sub(r'"[\s]*"', '", "', json_string)
        
        try:
            json_object = json5.loads(json_string)
        except ValueError:
            json_object = json5.loads(f"[{json_string}]")
        
        return json_object
    
    raise Exception("No JSON object found in input text.")


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
