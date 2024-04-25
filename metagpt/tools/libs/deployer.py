from metagpt.report import ServerReporter
from metagpt.tools.tool_registry import register_tool


# An un-implemented tool reserved for deploying a local service to public
@register_tool()
class Deployer:
    """Deploy a local service to public. Used only for final deployment, you should NOT use it for development and testing."""

    def deploy_to_public(self, local_url: str):
        ServerReporter().report(local_url, "local_url")
