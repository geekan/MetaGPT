# Dev Container

This project includes a [Dev Container](https://containers.dev/), offering you a comprehensive and fully-featured development environment within a container. By leveraging the Dev Container configuration in this folder, you can seamlessly build and initiate MetaGPT locally. For detailed information, please refer to the main README in the home directory.

You can utilize this Dev Container in [GitHub Codespaces](https://github.com/features/codespaces) or with the [VS Code Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

## GitHub Codespaces
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/geekan/MetaGPT)

Click the button above to open this repository in a Codespace. For additional information, refer to the [GitHub documentation on creating a Codespace](https://docs.github.com/en/free-pro-team@latest/github/developing-online-with-codespaces/creating-a-codespace#creating-a-codespace).

## VS Code Dev Containers
[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/geekan/MetaGPT)

Note: Clicking the link above opens the main repository. To open your local cloned repository, replace the URL with your username and cloned repository's name: `https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/<your-username>/<your-repo-name>`

If you have VS Code and Docker installed, use the button above to get started. This will prompt VS Code to install the Dev Containers extension if it's not already installed, clone the source code into a container volume, and set up a dev container for you.

Alternatively, follow these steps to open this repository in a container using the VS Code Dev Containers extension:

1. For first-time users of a development container, ensure your system meets the prerequisites (e.g., Docker installation) as outlined in the [getting started steps](https://aka.ms/vscode-remote/containers/getting-started).

2. To open a locally cloned copy of the code:
   - Fork and clone this repository to your local file system.
   - Press <kbd>F1</kbd> and select the **Dev Containers: Open Folder in Container...** command.
   - Choose the cloned folder, wait for the container to initialize, and start exploring!

Learn more in the [VS Code Dev Containers documentation](https://code.visualstudio.com/docs/devcontainers/containers).

## Tips and Tricks

* When working with the same repository folder in both a container and on Windows, it's crucial to have consistent line endings to avoid numerous changes in the SCM view. The `.gitattributes` file in the root of this repository disables line ending conversion, helping to prevent this issue. For more information, see [resolving git line ending issues in containers](https://code.visualstudio.com/docs/devcontainers/tips-and-tricks#_resolving-git-line-ending-issues-in-containers-resulting-in-many-modified-files).

* If you're curious about the contents of the image used in this Dev Container, you can review it in the [devcontainers/images](https://github.com/devcontainers/images/tree/main/src/python) repository.
