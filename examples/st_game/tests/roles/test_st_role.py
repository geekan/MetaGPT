from examples.st_game.roles.st_role import STRole, STRoleContext
from examples.st_game.memory.agent_memory import BasicMemory

role = STRole(start_date="October 4, 2023", curr_time="October 4, 2023, 00:00:00", 
                sim_code="base_the_ville_isabella_maria_klaus")

def test_role_init():
    assert role.role_tile == (126, 46)
    assert role._rc.env.maze.maze_height == 100
    assert role._rc.env.maze.maze_width == 140

def test_observe():
    ret_events = role.observe()
    assert ret_events
    for event in ret_events:
        assert isinstance(event, BasicMemory)