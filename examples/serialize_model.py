from metagpt.logs import logger
from metagpt.roles.product_manager import ProductManager


def main():
    """Demonstrates serialization and deserialization using SerializationMixin.

    This example creates an instance of ProductManager, serializes it to a file,
    and then deserializes it back to an instance.

    If executed correctly, the following log messages will be output:
        ProductManager serialization successful. File saved at: /data/hjt/gitlab_metagpt/workspace/storage/ProductManager.json
        ProductManager deserialization successful. Instance created from file: /data/hjt/gitlab_metagpt/workspace/storage/ProductManager.json
        The role is Product Manager
    """
    role = ProductManager()
    role.serialize()

    role: ProductManager = ProductManager.deserialize()
    logger.info(f"The role is {role.profile}")


if __name__ == "__main__":
    main()
