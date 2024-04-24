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
        goal="Take on any data-related tasks, such as data analysis, machine learning, deep learning, web browsing, web scraping, web deployment, terminal operation, git operation, etc.",
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

    tl = env.get_role("Team Leader")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    # TL should assign tasks to 5 members first, then send message to the first assignee, 6 commands in total
    assert len(tl.commands) == 6
    plan_cmd = tl.commands[:5]
    route_cmd = tl.commands[5]

    task_assignment = [task["args"]["assignee"] for task in plan_cmd]
    assert task_assignment == [
        ProductManager().name,
        Architect().name,
        ProjectManager().name,
        Engineer().name,
        QaEngineer().name,
    ]

    assert route_cmd["command_name"] == "publish_message"
    assert route_cmd["args"]["send_to"] == ProductManager().name


@pytest.mark.asyncio
async def test_plan_for_data_related_requirement(env):
    requirement = "I want to use yolov5 for target detection, yolov5 all the information from the following link, please help me according to the content of the link (https://github.com/ultralytics/yolov5), set up the environment and download the model parameters, and finally provide a few pictures for inference, the inference results will be saved!"

    tl = env.get_role("Team Leader")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    # TL should assign 1 task to Data Analyst and send message to it
    assert len(tl.commands) == 2
    plan_cmd = tl.commands[0]
    route_cmd = tl.commands[-1]

    da = env.get_role("Data Analyst")
    assert plan_cmd["command_name"] == "append_task"
    assert plan_cmd["args"]["assignee"] == da.name

    assert route_cmd["command_name"] == "publish_message"
    assert "https://github.com" in route_cmd["args"]["content"]  # necessary info must be in the message
    assert route_cmd["args"]["send_to"] == da.name


@pytest.mark.asyncio
async def test_plan_for_mixed_requirement(env):
    requirement = "Search the web for the new game 2048X, then replicate it"

    tl = env.get_role("Team Leader")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    # TL should assign 6 tasks, first to Data Analyst to search the web, following by the software team sequence
    # TL should send message to Data Analyst after task assignment
    assert len(tl.commands) == 7
    plan_cmd = tl.commands[:6]
    route_cmd = tl.commands[-1]

    task_assignment = [task["args"]["assignee"] for task in plan_cmd]
    da = env.get_role("Data Analyst")
    assert task_assignment == [
        da.name,
        ProductManager().name,
        Architect().name,
        ProjectManager().name,
        Engineer().name,
        QaEngineer().name,
    ]

    assert route_cmd["command_name"] == "publish_message"
    assert route_cmd["args"]["send_to"] == da.name


PRD_MSG_CONTENT = """{'docs': {'20240424153821.json': {'root_path': 'docs/prd', 'filename': '20240424153821.json', 'content': '{"Language":"en_us","Programming Language":"Python","Original Requirements":"create a 2048 game","Project Name":"game_2048","Product Goals":["Develop an intuitive and addictive 2048 game variant","Ensure the game is accessible and performs well on various devices","Design a visually appealing and modern user interface"],"User Stories":["As a player, I want to be able to undo my last move so I can correct mistakes","As a player, I want to see my high scores to track my progress over time","As a player, I want to be able to play the game without any internet connection"],"Competitive Analysis":["2048 Original: Classic gameplay, minimalistic design, lacks social sharing features","2048 Hex: Unique hexagon board, but not mobile-friendly","2048 Multiplayer: Offers real-time competition, but overwhelming ads","2048 Bricks: Innovative gameplay with bricks, but poor performance on older devices","2048.io: Multiplayer battle royale mode, but complicated UI for new players","2048 Animated: Animated tiles add fun, but the game consumes a lot of battery","2048 3D: 3D version of the game, but has a steep learning curve"],"Competitive Quadrant Chart":"quadrantChart\\n    title \\"User Experience and Feature Set of 2048 Games\\"\\n    x-axis \\"Basic Features\\" --> \\"Rich Features\\"\\n    y-axis \\"Poor Experience\\" --> \\"Great Experience\\"\\n    quadrant-1 \\"Need Improvement\\"\\n    quadrant-2 \\"Feature-Rich but Complex\\"\\n    quadrant-3 \\"Simplicity with Poor UX\\"\\n    quadrant-4 \\"Balanced\\"\\n    \\"2048 Original\\": [0.2, 0.7]\\n    \\"2048 Hex\\": [0.3, 0.4]\\n    \\"2048 Multiplayer\\": [0.6, 0.5]\\n    \\"2048 Bricks\\": [0.4, 0.3]\\n    \\"2048.io\\": [0.7, 0.4]\\n    \\"2048 Animated\\": [0.5, 0.6]\\n    \\"2048 3D\\": [0.6, 0.3]\\n    \\"Our Target Product\\": [0.8, 0.9]","Requirement Analysis":"The game must be engaging and retain players, which requires a balance of simplicity and challenge. Accessibility on various devices is crucial for a wider reach. A modern UI is needed to attract and retain the modern user. The ability to play offline is important for users on the go. High score tracking and the ability to undo moves are features that will enhance user experience.","Requirement Pool":[["P0","Implement core 2048 gameplay mechanics"],["P0","Design responsive UI for multiple devices"],["P1","Develop undo move feature"],["P1","Integrate high score tracking system"],["P2","Enable offline gameplay capability"]],"UI Design draft":"The UI will feature a clean and modern design with a minimalist color scheme. The game board will be center-aligned with smooth tile animations. Score and high score will be displayed at the top. Undo and restart buttons will be easily accessible. The design will be responsive to fit various screen sizes.","Anything UNCLEAR":"The monetization strategy for the game is not specified. Further clarification is needed on whether the game should include advertisements, in-app purchases, or be completely free."}'}}}"""
DESIGN_CONTENT = """{"docs":{"20240424214432.json":{"root_path":"docs/system_design","filename":"20240424214432.json","content":"{\\"Implementation approach\\":\\"We will develop the 2048 game using Python, leveraging the pygame library for rendering the game interface and handling user input. This library is suitable for creating games and is widely used in the open-source community. We will ensure that the game logic is separated from the UI code to maintain a clean architecture. The game will be designed to be responsive and accessible on both desktop and mobile devices using scalable dimensions and touch-friendly controls.\\",\\"File list\\":[\\"main.py\\",\\"game.py\\",\\"ui.py\\",\\"constants.py\\",\\"logic.py\\"],\\"Data structures and interfaces\\":\\"\\\\nclassDiagram\\\\n    class Main {\\\\n        +main() void\\\\n    }\\\\n    class Game {\\\\n        -UI ui\\\\n        -Logic logic\\\\n        +start_game() void\\\\n        +restart_game() void\\\\n    }\\\\n    class UI {\\\\n        -current_score int\\\\n        -high_score int\\\\n        +draw_board(board: list) void\\\\n        +update_score(score: int) void\\\\n        +show_game_over() void\\\\n    }\\\\n    class Logic {\\\\n        -board list\\\\n        -score int\\\\n        +move(direction: str) bool\\\\n        +check_game_over() bool\\\\n        +get_current_score() int\\\\n        +get_high_score() int\\\\n        +reset_game() void\\\\n    }\\\\n    class Constants {\\\\n        +BOARD_SIZE int\\\\n        +INITIAL_TILES int\\\\n    }\\\\n    Main --> Game\\\\n    Game --> UI\\\\n    Game --> Logic\\\\n\\",\\"Program call flow\\":\\"\\\\nsequenceDiagram\\\\n    participant M as Main\\\\n    participant G as Game\\\\n    participant UI as UI\\\\n    participant L as Logic\\\\n    M->>G: start_game()\\\\n    loop Game Loop\\\\n        G->>UI: draw_board(board)\\\\n        G->>L: move(direction)\\\\n        alt if move successful\\\\n            L-->>G: return true\\\\n            G->>UI: update_score(score)\\\\n        else if move not successful\\\\n            L-->>G: return false\\\\n        end\\\\n        G->>L: check_game_over()\\\\n        alt if game over\\\\n            L-->>G: return true\\\\n            G->>UI: show_game_over()\\\\n            G->>G: restart_game()\\\\n        else\\\\n            L-->>G: return false\\\\n        end\\\\n    end\\\\n\\",\\"Anything UNCLEAR\\":\\"Clarification needed on the specific touch-friendly controls for mobile devices and how they will be implemented using pygame.\\"}"}}}"""


@pytest.mark.asyncio
async def test_plan_update_and_routing(env):
    requirement = "create a 2048 game"

    tl = env.get_role("Team Leader")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    # Assuming Product Manager finishes its task
    env.publish_message(Message(content=PRD_MSG_CONTENT, role="Alice(Product Manager)", sent_from="Alice"))
    await tl.run()

    # TL should mark current task as finished, and forward Product Manager's message to Architect
    plan_cmd = tl.commands[0]
    route_cmd = tl.commands[-1]
    assert plan_cmd["command_name"] == "finish_current_task"
    assert route_cmd["command_name"] == "forward_message" or route_cmd["command_name"] == "publish_message"


async def main():
    requirement = [
        # "Create a cli snake game",
        # "I want to use yolov5 for target detection, yolov5 all the information from the following link, please help me according to the content of the link(https://github.com/ultralytics/yolov5), set up the environment and download the model parameters, and finally provide a few pictures for inference, the inference results will be saved!",
        # "Create a website widget for TODO list management. Users should be able to add, mark as complete, and delete tasks. Include features like prioritization, due dates, and categories. Make it visually appealing, responsive, and user-friendly. Use HTML, CSS, and JavaScript. Consider additional features like notifications or task export. Keep it simple and enjoyable for users.dont use vue or react.dont use third party library, use localstorage to save data",
        # "Search the web for the new game 2048X, then replicate it",
        # """从36kr创投平台https://pitchhub.36kr.com/financing-flash 所有初创企业融资的信息, **注意: 这是一个中文网站**;
        # 下面是一个大致流程, 你会根据每一步的运行结果对当前计划中的任务做出适当调整:
        # 1. 爬取并本地保存html结构;
        # 2. 直接打印第7个*`快讯`*关键词后2000个字符的html内容, 作为*快讯的html内容示例*;
        # 3. 反思*快讯的html内容示例*中的规律, 设计正则匹配表达式来获取*`快讯`*的标题、链接、时间;
        # 4. 筛选最近3天的初创企业融资*`快讯`*, 以list[dict]形式打印前5个。
        # 5. 将全部结果存在本地csv中
        # """,
        """
        I would like to imitate the website available at  https://news.youth.cn/gn/202404/t20240406_15178916.htm. Could you please browse through it?
        Note:
        - don't ignore the image, use https://source.unsplash.com/random to get random images
        - use the same text, the same layout, the same color as the original website
        if you can not do it, please try to get as close as possible.
        """,
    ]
    tl.put_message(Message(requirement[0]))
    await tl._observe()
    await tl._think()


# asyncio.run(main())
