"""Setup script for MetaGPT."""
import subprocess
from pathlib import Path

from setuptools import Command, find_packages, setup


class InstallMermaidCLI(Command):
    """A custom command to run `npm install -g @mermaid-js/mermaid-cli` via a subprocess."""

    description = "install mermaid-cli"
    user_options = []

    def run(self):
        try:
            subprocess.check_call(["npm", "install", "-g", "@mermaid-js/mermaid-cli"])
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e.output}")


here = Path(__file__).resolve().parent
long_description = (here / "README.md").read_text(encoding="utf-8")
requirements = (here / "requirements.txt").read_text(encoding="utf-8").splitlines()


extras_require = {
    "selenium": ["selenium>4", "webdriver_manager", "beautifulsoup4"],
    "search-google": ["google-api-python-client==2.94.0"],
    "search-ddg": ["duckduckgo-search~=4.1.1"],
    "ocr": ["paddlepaddle==2.4.2", "paddleocr~=2.7.3", "tabulate==0.9.0"],
    "rag": [
        "llama-index-core==0.10.15",
        "llama-index-embeddings-azure-openai==0.1.6",
        "llama-index-embeddings-openai==0.1.5",
        "llama-index-embeddings-gemini==0.1.6",
        "llama-index-embeddings-ollama==0.1.2",
        "llama-index-llms-azure-openai==0.1.4",
        "llama-index-readers-file==0.1.4",
        "llama-index-retrievers-bm25==0.1.3",
        "llama-index-vector-stores-faiss==0.1.1",
        "llama-index-vector-stores-elasticsearch==0.1.6",
        "llama-index-vector-stores-chroma==0.1.6",
        "llama-index-postprocessor-cohere-rerank==0.1.4",
        "llama-index-postprocessor-colbert-rerank==0.1.1",
        "llama-index-postprocessor-flag-embedding-reranker==0.1.2",
        "docx2txt==0.8",
    ],
    "android_assistant": [
        "pyshine==0.0.9",
        "opencv-python==4.6.0.66",
        "protobuf<3.20,>=3.9.2",
        "modelscope",
        "tensorflow==2.9.1; os_name == 'linux'",
        "tensorflow==2.9.1; os_name == 'win32'",
        "tensorflow-macos==2.9; os_name == 'darwin'",
        "keras==2.9.0",
        "torch",
        "torchvision",
        "transformers",
        "opencv-python",
        "matplotlib",
        "pycocotools",
        "SentencePiece",
        "tf_slim",
        "tf_keras",
        "pyclipper",
        "shapely",
        "groundingdino-py",
        "datasets==2.18.0",
        "clip-openai",
    ],
}

extras_require["test"] = [
    *set(i for j in extras_require.values() for i in j),
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "pytest-mock",
    "pytest-html",
    "pytest-xdist",
    "pytest-timeout",
    "connexion[uvicorn]~=3.0.5",
    "azure-cognitiveservices-speech~=1.31.0",
    "aioboto3~=12.4.0",
    "gradio==3.0.0",
    "grpcio-status==1.48.2",
    "pylint==3.0.3",
    "pybrowsers",
]

extras_require["pyppeteer"] = [
    "pyppeteer>=1.0.2"
]  # pyppeteer is unmaintained and there are conflicts with dependencies
extras_require["dev"] = (["pylint~=3.0.3", "black~=23.3.0", "isort~=5.12.0", "pre-commit~=3.6.0"],)


setup(
    name="metagpt",
    version="0.8.1",
    description="The Multi-Agent Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geekan/MetaGPT",
    author="Alexander Wu",
    author_email="alexanderwu@deepwisdom.ai",
    license="MIT",
    keywords="metagpt multi-agent multi-role programming gpt llm metaprogramming",
    packages=find_packages(exclude=["contrib", "docs", "examples", "tests*"]),
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require=extras_require,
    cmdclass={
        "install_mermaid": InstallMermaidCLI,
    },
    entry_points={
        "console_scripts": [
            "metagpt=metagpt.software_company:app",
        ],
    },
    include_package_data=True,
)
