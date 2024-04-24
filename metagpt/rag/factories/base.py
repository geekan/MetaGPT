"""Base Factory."""

from typing import Any, Callable


class GenericFactory:
    """Designed to get objects based on any keys."""

    def __init__(self, creators: dict[Any, Callable] = None):
        """Creators is a dictionary.

        Keys are identifiers, and the values are the associated creator function, which create objects.
        """
        self._creators = creators or {}

    def get_instances(self, keys: list[Any], **kwargs) -> list[Any]:
        """Get instances by keys."""
        return [self.get_instance(key, **kwargs) for key in keys]

    def get_instance(self, key: Any, **kwargs) -> Any:
        """Get instance by key.

        Raise Exception if key not found.
        """
        creator = self._creators.get(key)
        if creator:
            return creator(**kwargs)

        self._raise_for_key(key)

    def _raise_for_key(self, key: Any):
        raise ValueError(f"Creator not registered for key: {key}")


class ConfigBasedFactory(GenericFactory):
    """Designed to get objects based on object type."""

    def get_instance(self, key: Any, **kwargs) -> Any:
        """Get instance by the type of key.

        Key is config, such as a pydantic model, call func by the type of key, and the key will be passed to func.
        Raise Exception if key not found.
        """
        creator = self._creators.get(type(key))
        if creator:
            return creator(key, **kwargs)

        self._raise_for_key(key)

    def _raise_for_key(self, key: Any):
        raise ValueError(f"Unknown config: `{type(key)}`, {key}")

    @staticmethod
    def _val_from_config_or_kwargs(key: str, config: object = None, **kwargs) -> Any:
        """It prioritizes the configuration object's value unless it is None, in which case it looks into kwargs.

        Return None if not found.
        """
        if config is not None and hasattr(config, key):
            val = getattr(config, key)
            if val is not None:
                return val

        if key in kwargs:
            return kwargs[key]

        return None
