import pytest

from metagpt.actions.write_plan import WritePlan


@pytest.mark.asyncio
async def test_plan():
    p = WritePlan()
    task_desc = """Here’s some background information on Cyclistic, a bike-sharing company designing a marketing strategy aimed at converting casual riders into annual members: So far, Cyclistic’s marketing strategy has relied on building general awareness and engaging a wide range of consumers. group. One way to help achieve these goals is the flexibility of its pricing plans: one-way passes, full-day passes, and annual memberships. Customers who purchase a one-way or full-day pass are known as recreational riders. Customers purchasing an annual membership are Cyclistic members. I will provide you with a data sheet that records user behavior: '/Users/vicis/Downloads/202103-divvy-tripdata.csv"""
    rsp = await p.run(task_desc, role="data analyst")
    assert len(rsp.content) > 0
    assert rsp.sent_from == "WritePlan"
    print(rsp)
