from metagpt.utils.reflection import get_func_or_method_name


def simple_function():
    pass


class SampleClass:
    def method(self):
        pass


class TestFunctionOrMethodName:
    def test_simple_function(self):
        assert get_func_or_method_name(simple_function) == "simple_function"

    def test_class_method_without_args(self):
        sample_instance = SampleClass()
        assert get_func_or_method_name(sample_instance.method) == "SampleClass.method"

    def test_class_method_with_args(self):
        sample_instance = SampleClass()
        assert get_func_or_method_name(SampleClass.method, sample_instance) == "SampleClass.method"

    def test_function_with_no_args(self):
        assert get_func_or_method_name(simple_function) == "simple_function"

    def test_method_without_instance(self):
        assert get_func_or_method_name(SampleClass.method) == "method"
