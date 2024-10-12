from metagpt.tools.tool_registry import register_tool


# An un-implemented tool reserved for deploying a local service to public
@register_tool(
    include_functions=[
        "deploy_to_public",
    ]
)
class Deployer:
    """Deploy a local service to public. Used only for final deployment, you should NOT use it for development and testing."""

    async def static_server(self, src_path: str) -> str:
        """This function will be implemented in the remote service."""
        return "http://127.0.0.1:8000/index.html"

    async def deploy_to_public(self, dist_dir: str):
        """
        Deploy a web project to public.
        Args:
            dist_dir (str): The dist directory of the web project after run build.
        >>>
            deployer = Deployer("2048_game/dist")
        """
        url = await self.static_server(dist_dir)
        return "The Project is deployed to: " + url + "\n Deployment successed!"
