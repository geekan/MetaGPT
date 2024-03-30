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

        raise ValueError(f"Creator not registered for key: {key}")


class ConfigBasedFactory(GenericFactory):
    """Designed to get objects based on object type."""

    def get_instance(self, key: Any, **kwargs) -> Any:
        """Key is config, such as a pydantic model.

        Call func by the type of key, and the key will be passed to func.
        """
        creator = self._creators.get(type(key))
        if creator:
            return creator(key, **kwargs)

        raise ValueError(f"Unknown config: `{type(key)}`, {key}")

    @staticmethod
    def _val_from_config_or_kwargs(key: str, config: object = None, **kwargs) -> Any:
        """It prioritizes the configuration object's value unless it is None, in which case it looks into kwargs."""
        if config is not None and hasattr(config, key):
            val = getattr(config, key)
            if val is not None:
                return val

        if key in kwargs:
            return kwargs[key]

        raise KeyError(
            f"The key '{key}' is required but not provided in either configuration object or keyword arguments."
        )
