#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : st's reflection execution

import asyncio
import json
import time
from metagpt.logs import logger
from ..prompts.wrapper_prompt import special_response_generate
from ..memory.agent_memory import BasicMemory


async def agent_reflect(memories_list):
    """
    代理反思函数：生成关注点并生成洞察和证据

    """
    A = await generate_focus_point(memories_list)

    for i in A:
        B = await generate_insights_and_evidence(memories_list, question=i)


async def generate_focus_point(memories_list: list[MemoryBasic], n=3):
    """
    生成关注点函数：根据记忆列表生成关注点
    """
    wait_sorted_mem = [[i.accessed_time, i] for i in memories_list]
    sorted_memories = sorted(wait_sorted_mem, key=lambda x: x[0])
    memorys = [i for created, i in sorted_memories]
    statements = ''
    for i in memorys:
        statements += i.description + "\n"
    prompt = '''
    {statements}
    Given only the information above, what are {num_question} most salient high-level questions we can answer about the subjects grounded in the statements?
    '''
    example_output = '["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
    out = await final_response(prompt.format(statements=statements, num_question=n),
                               "Output must be a list of str.", example_output)
    try:
        poi_dict = json.loads(out)
        return poi_dict['output']
    except ValueError:
        print(out)
        logger.error('无法返回正常结果')
        return out


async def generate_insights_and_evidence(memories_list: list[MemoryBasic], question: str, n=5):
    """
    生成洞察和证据函数：根据问题生成洞察和证据
    """
    memories_list = await agent_retrieve(agent, question, 50, 10)
    statements = ""
    for count, mem in enumerate(memories_list):
        statements += f'{str(count)}. {mem.description}\n'
    prompt = '''
    Input:
    {statements}

    What {n} high-level insights can you infer from the above statements?
    You should return a list of list[str,list]. The first element is the insight you have found. The second element is the 
    '''

    ret = final_response(prompt.format(
        question=question, statements=statements, n=n), "['insightA',[1,2,3]]")
    try:
        insight_list = json.loads(ret)
        for insight, index in insight_list:
            agent.memory_list.append(MemoryBasic(
                time.time(), None, insight, None, None))
        return insight_list
    except:
        logger.error('我们无法获得想要的返回。')
        return ret


""" if __name__ == "__main__":
    # 例子，构建John Agent，实现retrive
    John_iss = "John Lin is a pharmacy shopkeeper at the Willow Market and Pharmacy who loves to help people. He is always looking for ways to make the process of getting medication easier for his customers; John Lin is living with his wife, Mei Lin, who is a college professor, and son, Eddy Lin, who is a student studying music theory; John Lin loves his family very much; John Lin has known the old couple next-door, Sam Moore and Jennifer Moore, for a few years; John Lin thinks Sam Moore is a kind and nice man; John Lin knows his neighbor, Yuriko Yamamoto, well; John Lin knows of his neighbors, Tamara Taylor and Carmen Ortiz, but has not met them before; John Lin and Tom Moreno are colleagues at The Willows Market and Pharmacy; John Lin and Tom Moreno are friends and like to discuss local politics together; John Lin knows the Moreno family somewhat well — the husband Tom Moreno and the wife Jane Moreno."
    John = AgentMemory(
        "John", John_iss, memory_path="agent_memories/John_memory.json")

    # John的相关信息：{'Had a friendly chat with Yuriko about her garden.': 2.4992317730827667, 'Helped Mrs. Moore carry groceries into her house.': 1.957656720441911, 'Discussed local politics with Tom Moreno.': 1.9458268038234035}
    asyncio.run(agent_reflect(John))
    '''
    这里是输出,list形式，返回给记忆。
    [['The pharmacy is a friendly and helpful community.', [0, 2, 9, 12]], ['The pharmacy is a place where people come for more than just medication.', [3, 5, 13, 14]], ['The pharmacy is a place where people come for advice and conversation.', [0, 2, 6, 9, 12]], ['The pharmacy is a place where people come for assistance with daily tasks.', [3, 5, 13, 14]], ['The pharmacy is a place where people come for political discussions.', [1]]]
    '''
 """
