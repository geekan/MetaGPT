import pytest

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
)
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message


@pytest.fixture
def env():
    test_env = MGXEnv()
    tl = TeamLeader()
    da = DataInterpreter(
        name="David",
        profile="Data Analyst",
        goal="Take on any data-related tasks, such as data analysis, machine learning, deep learning, web browsing, web scraping, web searching, web deployment, terminal operation, git operation, etc.",
        react_mode="react",
    )
    test_env.add_roles(
        [
            tl,
            ProductManager(),
            Architect(),
            ProjectManager(),
            Engineer(n_borg=5, use_code_review=True),
            QaEngineer(),
            da,
        ]
    )
    return test_env


@pytest.mark.asyncio
async def test_plan_for_software_requirement(env):
    requirement = "create a 2048 game"
    tl = env.get_role("Mike")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    history = env.history.get()

    messages_to_team = [msg for msg in history if msg.sent_from == tl.name]
    pm_messages = [msg for msg in messages_to_team if "Alice" in msg.send_to]
    assert len(pm_messages) > 0, "Should have message sent to Product Manager"
    found_task_msg = False
    for msg in messages_to_team:
        if "prd" in msg.content.lower() and any(role in msg.content for role in ["Alice", "Bob", "Alex", "David"]):
            found_task_msg = True
            break
    assert found_task_msg, "Should have task assignment message"


@pytest.mark.asyncio
async def test_plan_for_data_related_requirement(env):
    requirement = "I want to use yolov5 for target detection, yolov5 all the information from the following link, please help me according to the content of the link (https://github.com/ultralytics/yolov5), set up the environment and download the model parameters, and finally provide a few pictures for inference, the inference results will be saved!"

    tl = env.get_role("Mike")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    history = env.history.get()
    messages_from_tl = [msg for msg in history if msg.sent_from == tl.name]
    da_messages = [msg for msg in messages_from_tl if "David" in msg.send_to]
    assert len(da_messages) > 0

    da_message = da_messages[0]
    assert "https://github.com/ultralytics/yolov5" in da_message.content

    def is_valid_task_message(msg: Message) -> bool:
        content = msg.content.lower()
        has_model_info = "yolov5" in content
        has_task_info = any(word in content for word in ["detection", "inference", "environment", "parameters"])
        has_link = "github.com" in content
        return has_model_info and has_task_info and has_link

    assert is_valid_task_message(da_message)


@pytest.mark.asyncio
async def test_plan_for_mixed_requirement(env):
    requirement = "Search the web for the new game 2048X, then replicate it"

    tl = env.get_role("Mike")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    history = env.history.get()
    messages_from_tl = [msg for msg in history if msg.sent_from == tl.name]

    da_messages = [msg for msg in messages_from_tl if "David" in msg.send_to]
    assert len(da_messages) > 0

    da_message = da_messages[0]

    def is_valid_search_task(msg: Message) -> bool:
        content = msg.content.lower()
        return "2048x" in content and "search" in content

    assert is_valid_search_task(da_message)


PRD_MSG_CONTENT = """{'docs': {'20240424153821.json': {'root_path': 'docs/prd', 'filename': '20240424153821.json', 'content': '{"Language":"en_us","Programming Language":"Python","Original Requirements":"create a 2048 game","Project Name":"game_2048","Product Goals":["Develop an intuitive and addictive 2048 game variant","Ensure the game is accessible and performs well on various devices","Design a visually appealing and modern user interface"],"User Stories":["As a player, I want to be able to undo my last move so I can correct mistakes","As a player, I want to see my high scores to track my progress over time","As a player, I want to be able to play the game without any internet connection"],"Competitive Analysis":["2048 Original: Classic gameplay, minimalistic design, lacks social sharing features","2048 Hex: Unique hexagon board, but not mobile-friendly","2048 Multiplayer: Offers real-time competition, but overwhelming ads","2048 Bricks: Innovative gameplay with bricks, but poor performance on older devices","2048.io: Multiplayer battle royale mode, but complicated UI for new players","2048 Animated: Animated tiles add fun, but the game consumes a lot of battery","2048 3D: 3D version of the game, but has a steep learning curve"],"Competitive Quadrant Chart":"quadrantChart\\n    title \\"User Experience and Feature Set of 2048 Games\\"\\n    x-axis \\"Basic Features\\" --> \\"Rich Features\\"\\n    y-axis \\"Poor Experience\\" --> \\"Great Experience\\"\\n    quadrant-1 \\"Need Improvement\\"\\n    quadrant-2 \\"Feature-Rich but Complex\\"\\n    quadrant-3 \\"Simplicity with Poor UX\\"\\n    quadrant-4 \\"Balanced\\"\\n    \\"2048 Original\\": [0.2, 0.7]\\n    \\"2048 Hex\\": [0.3, 0.4]\\n    \\"2048 Multiplayer\\": [0.6, 0.5]\\n    \\"2048 Bricks\\": [0.4, 0.3]\\n    \\"2048.io\\": [0.7, 0.4]\\n    \\"2048 Animated\\": [0.5, 0.6]\\n    \\"2048 3D\\": [0.6, 0.3]\\n    \\"Our Target Product\\": [0.8, 0.9]","Requirement Analysis":"The game must be engaging and retain players, which requires a balance of simplicity and challenge. Accessibility on various devices is crucial for a wider reach. A modern UI is needed to attract and retain the modern user. The ability to play offline is important for users on the go. High score tracking and the ability to undo moves are features that will enhance user experience.","Requirement Pool":[["P0","Implement core 2048 gameplay mechanics"],["P0","Design responsive UI for multiple devices"],["P1","Develop undo move feature"],["P1","Integrate high score tracking system"],["P2","Enable offline gameplay capability"]],"UI Design draft":"The UI will feature a clean and modern design with a minimalist color scheme. The game board will be center-aligned with smooth tile animations. Score and high score will be displayed at the top. Undo and restart buttons will be easily accessible. The design will be responsive to fit various screen sizes.","Anything UNCLEAR":"The monetization strategy for the game is not specified. Further clarification is needed on whether the game should include advertisements, in-app purchases, or be completely free."}'}}}"""
DESIGN_CONTENT = """{"docs":{"20240424214432.json":{"root_path":"docs/system_design","filename":"20240424214432.json","content":"{\\"Implementation approach\\":\\"We will develop the 2048 game using Python, leveraging the pygame library for rendering the game interface and handling user input. This library is suitable for creating games and is widely used in the open-source community. We will ensure that the game logic is separated from the UI code to maintain a clean architecture. The game will be designed to be responsive and accessible on both desktop and mobile devices using scalable dimensions and touch-friendly controls.\\",\\"File list\\":[\\"main.py\\",\\"game.py\\",\\"ui.py\\",\\"constants.py\\",\\"logic.py\\"],\\"Data structures and interfaces\\":\\"\\\\nclassDiagram\\\\n    class Main {\\\\n        +main() void\\\\n    }\\\\n    class Game {\\\\n        -UI ui\\\\n        -Logic logic\\\\n        +start_game() void\\\\n        +restart_game() void\\\\n    }\\\\n    class UI {\\\\n        -current_score int\\\\n        -high_score int\\\\n        +draw_board(board: list) void\\\\n        +update_score(score: int) void\\\\n        +show_game_over() void\\\\n    }\\\\n    class Logic {\\\\n        -board list\\\\n        -score int\\\\n        +move(direction: str) bool\\\\n        +check_game_over() bool\\\\n        +get_current_score() int\\\\n        +get_high_score() int\\\\n        +reset_game() void\\\\n    }\\\\n    class Constants {\\\\n        +BOARD_SIZE int\\\\n        +INITIAL_TILES int\\\\n    }\\\\n    Main --> Game\\\\n    Game --> UI\\\\n    Game --> Logic\\\\n\\",\\"Program call flow\\":\\"\\\\nsequenceDiagram\\\\n    participant M as Main\\\\n    participant G as Game\\\\n    participant UI as UI\\\\n    participant L as Logic\\\\n    M->>G: start_game()\\\\n    loop Game Loop\\\\n        G->>UI: draw_board(board)\\\\n        G->>L: move(direction)\\\\n        alt if move successful\\\\n            L-->>G: return true\\\\n            G->>UI: update_score(score)\\\\n        else if move not successful\\\\n            L-->>G: return false\\\\n        end\\\\n        G->>L: check_game_over()\\\\n        alt if game over\\\\n            L-->>G: return true\\\\n            G->>UI: show_game_over()\\\\n            G->>G: restart_game()\\\\n        else\\\\n            L-->>G: return false\\\\n        end\\\\n    end\\\\n\\",\\"Anything UNCLEAR\\":\\"Clarification needed on the specific touch-friendly controls for mobile devices and how they will be implemented using pygame.\\"}"}}}"""


@pytest.mark.asyncio
async def test_plan_update_and_routing(env):
    requirement = "create a 2048 game"

    tl = env.get_role("Mike")
    env.publish_message(Message(content=requirement))
    await tl.run()

    # Verify message routing after PM completes task
    env.publish_message(Message(content=PRD_MSG_CONTENT, sent_from="Alice", send_to={"<all>"}))
    await tl.run()

    # Get message history
    history = env.history.get()
    messages_from_tl = [msg for msg in history if msg.sent_from == tl.name]

    # Verify messages sent to architect
    architect_messages = [msg for msg in messages_from_tl if "Bob" in msg.send_to]
    assert len(architect_messages) > 0, "Should have message forwarded to architect"

    # Verify message content contains PRD info
    architect_message = architect_messages[-1]
    assert "2048 game based on the PRD" in architect_message.content, "Message to architect should contain PRD info"

    # Verify message routing after architect completes task
    env.publish_message(Message(content=DESIGN_CONTENT, sent_from="Bob", send_to={"<all>"}))
    await tl.run()


@pytest.mark.asyncio
async def test_reply_to_human(env):
    requirement = "create a 2048 game"

    tl = env.get_role("Mike")
    env.publish_message(Message(content=requirement))
    await tl.run()

    # PM finishes task
    env.publish_message(Message(content=PRD_MSG_CONTENT, sent_from="Alice", send_to={"<all>"}))
    await tl.run()

    # Get history before human inquiry
    history_before = env.history.get()

    # Human inquires about progress
    env.publish_message(Message(content="Who is working? How does the project go?", send_to={tl.name}))
    await tl.run()

    # Get new messages after human inquiry
    history_after = env.history.get()
    new_messages = [msg for msg in history_after if msg not in history_before]

    # Verify team leader's response
    tl_responses = [msg for msg in new_messages if msg.sent_from == tl.name]
    assert len(tl_responses) > 0, "Should have response from team leader"

    # Verify response contains project status
    response = tl_responses[0].content
    assert any(
        keyword in response.lower() for keyword in ["progress", "status", "working"]
    ), "Response should contain project status information"
