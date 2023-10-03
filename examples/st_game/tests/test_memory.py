from datetime import datetime
from metagpt.logs import logger
from examples.st_game.memory.agent_memory import AgentMemory, BasicMemory

# Create some sample BasicMemory instances
memory1 = BasicMemory(
    memory_id="1",
    memory_count=1,
    type_count=1,
    memory_type="event",
    depth=1,
    created=datetime.now(),
    expiration=datetime.now(),
    subject="Subject1",
    predicate="Predicate1",
    object="Object1",
    content="This is content 1",
    embedding_key="embedding_key_1",
    poignancy=1,
    keywords=["keyword1", "keyword2"],
    filling=["memory_id_2"]
)

memory2 = BasicMemory(
    memory_id="2",
    memory_count=2,
    type_count=2,
    memory_type="thought",
    depth=2,
    created=datetime.now(),
    expiration=None,
    subject="Subject2",
    predicate="Predicate2",
    object="Object2",
    content="This is content 2",
    embedding_key="embedding_key_2",
    poignancy=2,
    keywords=["keyword3", "keyword4"],
    filling=[]
)

if __name__ == "__main__":
    # Create an AgentMemory instance and add the created BasicMemory instances
    agent_memory = AgentMemory(memory_saved="sample_memory_folder")
    agent_memory.add_event(memory1)
    agent_memory.add_thought(memory2)

    # Save the AgentMemory to a JSON file
    agent_memory.save("sample_memory_folder")

    # Load the AgentMemory from the JSON file
    loaded_agent_memory = AgentMemory(memory_saved="sample_memory_folder")

    # Get the summarized latest events
    latest_events = loaded_agent_memory.get_summarized_latest_events(retention=2)
    print("Summarized Latest Events:")
    for event in latest_events:
        print(event)

    # Get the last chat for a specific role
    last_chat = loaded_agent_memory.get_last_chat(target_role_name="role1")
    if last_chat:
        print(f"Last chat for role1: {last_chat.content}")
    else:
        print("No chat found for role1")
