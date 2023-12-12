import pytest

from metagpt.actions.write_plan import WritePlan, precheck_update_plan_from_rsp, Plan, Task

def test_precheck_update_plan_from_rsp():
    plan = Plan(goal="")
    plan.add_tasks([Task(task_id="1")])
    rsp = '[{"task_id": "2"}]'
    success, _ = precheck_update_plan_from_rsp(rsp, plan)
    assert success
    assert len(plan.tasks) == 1 and plan.tasks[0].task_id == "1"  # precheck should not change the original one

    invalid_rsp = 'wrong'
    success, _ = precheck_update_plan_from_rsp(invalid_rsp, plan)
    assert not success
