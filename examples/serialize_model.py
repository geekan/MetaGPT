from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.logs import logger


def main():
    """Demonstrates serialization and deserialization using SerializationMixin.

    This example creates an instance of MGXEnv, serializes it to a file,
    and then deserializes it back to an instance.

    If executed correctly, the following log messages will be output:
        MGXEnv serialization successful. File saved at: /.../workspace/storage/MGXEnv.json
        MGXEnv deserialization successful. Instance created from file: /.../workspace/storage/MGXEnv.json
        The instance is MGXEnv()
    """

    env = MGXEnv()
    env.serialize()

    env: MGXEnv = MGXEnv.deserialize()
    logger.info(f"The instance is {repr(env)}")


if __name__ == "__main__":
    main()
