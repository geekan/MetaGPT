import pytest

from metagpt.exp_pool.serializers.simple import SimpleSerializer


class TestSimpleSerializer:
    @pytest.fixture
    def serializer(self):
        return SimpleSerializer()

    def test_serialize_req(self, serializer: SimpleSerializer):
        # Test with different types of input
        assert serializer.serialize_req(req=123) == "123"
        assert serializer.serialize_req(req="test") == "test"
        assert serializer.serialize_req(req=[1, 2, 3]) == "[1, 2, 3]"
        assert serializer.serialize_req(req={"a": 1}) == "{'a': 1}"

    def test_serialize_resp(self, serializer: SimpleSerializer):
        # Test with different types of input
        assert serializer.serialize_resp(456) == "456"
        assert serializer.serialize_resp("response") == "response"
        assert serializer.serialize_resp([4, 5, 6]) == "[4, 5, 6]"
        assert serializer.serialize_resp({"b": 2}) == "{'b': 2}"

    def test_deserialize_resp(self, serializer: SimpleSerializer):
        # Test with different types of input
        assert serializer.deserialize_resp("789") == "789"
        assert serializer.deserialize_resp("test_response") == "test_response"
        assert serializer.deserialize_resp("[7, 8, 9]") == "[7, 8, 9]"
        assert serializer.deserialize_resp("{'c': 3}") == "{'c': 3}"

    def test_roundtrip(self, serializer: SimpleSerializer):
        # Test serialization and deserialization roundtrip
        original = "test_roundtrip"
        serialized = serializer.serialize_resp(original)
        deserialized = serializer.deserialize_resp(serialized)
        assert deserialized == original

    @pytest.mark.parametrize("input_value", [123, "test", [1, 2, 3], {"a": 1}, None])
    def test_serialize_req_types(self, serializer: SimpleSerializer, input_value):
        # Test serialize_req with various input types
        result = serializer.serialize_req(req=input_value)
        assert isinstance(result, str)
        assert result == str(input_value)
