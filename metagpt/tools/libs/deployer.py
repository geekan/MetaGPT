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
        # app = aiohttp.web.Application()
        # app.router.add_static('/', src_path, show_index=True)
        # runner = aiohttp.web.AppRunner(app)
        # await runner.setup()
        # site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
        # await site.start()
        # port = site._server.sockets[0].getsockname()[1]
        return f"http://127.0.0.1:{8000}/index.html"

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
