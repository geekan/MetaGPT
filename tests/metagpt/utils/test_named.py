import pytest

from metagpt.utils.named import Named


@pytest.mark.asyncio
async def test_suite():
    class A(Named):
        pass

    class B(A):
        pass

    assert A.get_class_name() == "tests.metagpt.utils.test_named.A"
    assert A().get_object_name() == "tests.metagpt.utils.test_named.A"
    assert B.get_class_name() == "tests.metagpt.utils.test_named.B"
    assert B().get_object_name() == "tests.metagpt.utils.test_named.B"


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
