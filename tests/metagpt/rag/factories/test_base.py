import pytest

from metagpt.rag.factories.base import ConfigBasedFactory, GenericFactory


class TestGenericFactory:
    @pytest.fixture
    def creators(self):
        return {
            "type1": lambda name: f"Instance of type1 with {name}",
            "type2": lambda name: f"Instance of type2 with {name}",
        }

    @pytest.fixture
    def factory(self, creators):
        return GenericFactory(creators=creators)

    def test_get_instance_success(self, factory):
        # Test successful retrieval of an instance
        key = "type1"
        instance = factory.get_instance(key, name="TestName")
        assert instance == "Instance of type1 with TestName"

    def test_get_instance_failure(self, factory):
        # Test failure to retrieve an instance due to unregistered key
        with pytest.raises(ValueError) as exc_info:
            factory.get_instance("unknown_key")
        assert "Creator not registered for key: unknown_key" in str(exc_info.value)

    def test_get_instances_success(self, factory):
        # Test successful retrieval of multiple instances
        keys = ["type1", "type2"]
        instances = factory.get_instances(keys, name="TestName")
        expected = ["Instance of type1 with TestName", "Instance of type2 with TestName"]
        assert instances == expected

    @pytest.mark.parametrize(
        "keys,expected_exception_message",
        [
            (["unknown_key"], "Creator not registered for key: unknown_key"),
            (["type1", "unknown_key"], "Creator not registered for key: unknown_key"),
        ],
    )
    def test_get_instances_with_failure(self, factory, keys, expected_exception_message):
        # Test failure to retrieve instances due to at least one unregistered key
        with pytest.raises(ValueError) as exc_info:
            factory.get_instances(keys, name="TestName")
        assert expected_exception_message in str(exc_info.value)


class DummyConfig:
    """A dummy config class for testing."""

    def __init__(self, name):
        self.name = name


class TestConfigBasedFactory:
    @pytest.fixture
    def config_creators(self):
        return {
            DummyConfig: lambda config, **kwargs: f"Processed {config.name} with {kwargs.get('extra', 'no extra')}",
        }

    @pytest.fixture
    def config_factory(self, config_creators):
        return ConfigBasedFactory(creators=config_creators)

    def test_get_instance_success(self, config_factory):
        # Test successful retrieval of an instance
        config = DummyConfig(name="TestConfig")
        instance = config_factory.get_instance(config, extra="additional data")
        assert instance == "Processed TestConfig with additional data"

    def test_get_instance_failure(self, config_factory):
        # Test failure to retrieve an instance due to unknown config type
        class UnknownConfig:
            pass

        config = UnknownConfig()
        with pytest.raises(ValueError) as exc_info:
            config_factory.get_instance(config)
        assert "Unknown config:" in str(exc_info.value)

    def test_val_from_config_or_kwargs_priority(self):
        # Test that the value from the config object has priority over kwargs
        config = DummyConfig(name="ConfigName")
        result = ConfigBasedFactory._val_from_config_or_kwargs("name", config, name="KwargsName")
        assert result == "ConfigName"

    def test_val_from_config_or_kwargs_fallback_to_kwargs(self):
        # Test fallback to kwargs when config object does not have the value
        config = DummyConfig(name=None)
        result = ConfigBasedFactory._val_from_config_or_kwargs("name", config, name="KwargsName")
        assert result == "KwargsName"

    def test_val_from_config_or_kwargs_key_error(self):
        # Test KeyError when the key is not found in both config object and kwargs
        config = DummyConfig(name=None)
        val = ConfigBasedFactory._val_from_config_or_kwargs("missing_key", config)
        assert val is None
