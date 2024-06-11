from metagpt.utils.reflection import get_class_name


class SimpleFunction:
    def function(self):
        pass


class SampleClass:
    @classmethod
    def class_method(cls):
        pass

    def instance_method(self):
        pass


def standalone_function():
    pass


class TestGetClassName:
    def test_instance_method(self):
        instance = SampleClass()
        assert get_class_name(instance.instance_method) == "SampleClass"

    def test_class_method(self):
        assert get_class_name(SampleClass.class_method) == "SampleClass"

    def test_standalone_function(self):
        assert get_class_name(standalone_function) == ""

    def test_function_within_simple_class(self):
        instance = SimpleFunction()
        assert get_class_name(instance.function) == "SimpleFunction"
