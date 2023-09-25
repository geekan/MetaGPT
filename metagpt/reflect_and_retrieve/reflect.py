
import json
from gpt_structure import final_response
from retrive import agent_retrive
'''
首先
'''
def agent_reflect(agent):
    '''
    agent:agent本身
    '''
    pass

def generate_focus_point(memories_list,n=3):
    wait_sorted_mem=[[i.accessed_time, i] for i in memories_list]
    sorted_memories=sorted(wait_sorted_mem, key=lambda x: x[0])
    memorys=[i for created, i in sorted_memories]
    statements=''
    for i in memorys:
        statements += i.description + "\n"
    prompt='''
    {statements}
    Given only the information above, what are {num_question} most salient high-level questions we can answer about the subjects grounded in the statements?
    '''
    example_output = '["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
    out = final_response(prompt.format(statements=statements,num_question=n), "Output must be a list of str.",example_output)
    try:
        poi_dict = json.loads(out)
        return (poi_dict['output'])
    except:
        return out

def generate_insights_and_evidence(agent,memories_list,question, n=5):
    agent_retrive(agent,question,20,10)
    statements = ""
    for count, mem in enumerate(memories_list): 
        statements += f'{str(count)}. {mem.description}\n'
    prompt='''
    Input:
    {statements}

    What {n} high-level insights can you infer from the above statements? (example format: insight (because of 1, 5, 3))
    1.'''
    
    ret = final_response(prompt.format(question=question,statements=statements,n=n), "['insightA',(1,2,3)]")
    print(ret)