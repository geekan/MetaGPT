from metagpt.schema import Plan, Task
from metagpt.strategy.planner import Planner
from metagpt.strategy.task_type import TaskType

MOCK_TASK_MAP = {
    "1": Task(
        task_id="1",
        instruction="test instruction for finished task",
        task_type=TaskType.EDA.type_name,
        dependent_task_ids=[],
        code="some finished test code",
        result="some finished test result",
        is_finished=True,
    ),
    "2": Task(
        task_id="2",
        instruction="test instruction for current task",
        task_type=TaskType.DATA_PREPROCESS.type_name,
        dependent_task_ids=["1"],
    ),
}
MOCK_PLAN = Plan(
    goal="test goal",
    tasks=list(MOCK_TASK_MAP.values()),
    task_map=MOCK_TASK_MAP,
    current_task_id="2",
)


def test_planner_get_plan_status():
    planner = Planner(plan=MOCK_PLAN)
    status = planner.get_plan_status()

    assert "some finished test code" in status
    assert "some finished test result" in status
    assert "test instruction for current task" in status
    assert TaskType.DATA_PREPROCESS.value.guidance in status  # current task guidance
