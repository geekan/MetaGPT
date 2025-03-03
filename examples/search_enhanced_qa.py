"""
This script demonstrates how to use the SearchEnhancedQA action to answer questions
by leveraging web search results. It showcases a simple example of querying about
the current weather in Beijing.

The SearchEnhancedQA action combines web search capabilities with natural language
processing to provide informative answers to user queries.
"""

import asyncio

from metagpt.actions.search_enhanced_qa import SearchEnhancedQA


async def main():
    """Runs a sample query through SearchEnhancedQA and prints the result."""

    action = SearchEnhancedQA()

    query = "What is the weather like in Beijing today?"
    answer = await action.run(query)

    print(f"The answer to '{query}' is:\n\n{answer}")


if __name__ == "__main__":
    asyncio.run(main())
