import re
from pathlib import Path

import pytest

from metagpt.utils.visual_graph_repo import VisualDiGraphRepo


@pytest.mark.asyncio
async def test_visual_di_graph_repo(context, mocker):
    filename = Path(__file__).parent / "../../data/graph_db/networkx.sequence_view.json"
    repo = await VisualDiGraphRepo.load_from(filename=filename)

    class_view = await repo.get_mermaid_class_view()
    assert class_view
    await context.repo.resources.graph_repo.save(filename="class_view.md", content=f"```mermaid\n{class_view}\n```\n")

    sequence_views = await repo.get_mermaid_sequence_views()
    assert sequence_views
    for ns, sqv in sequence_views:
        filename = re.sub(r"[:/\\\.]+", "_", ns) + ".sequence_view.md"
        await context.repo.resources.graph_repo.save(filename=filename, content=f"```mermaid\n{sqv}\n```\n")


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
