import os


def get_proxy_from_env():
    proxy_config = {}
    server = None
    for i in ("ALL_PROXY", "all_proxy", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        if os.environ.get(i):
            server = os.environ.get(i)
    if server:
        proxy_config["server"] = server
    no_proxy = os.environ.get("NO_PROXY") or os.environ.get("no_proxy")
    if no_proxy:
        proxy_config["bypass"] = no_proxy

    if not proxy_config:
        proxy_config = None

    return proxy_config
