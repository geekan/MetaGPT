import pytest


@pytest.fixture(autouse=True)
def llm_mock(rsp_cache, mocker, request):
    # An empty fixture to overwrite the global llm_mock fixture
    # because in provider folder, we want to test the aask and aask functions for the specific models
    pass
