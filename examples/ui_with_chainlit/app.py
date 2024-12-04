import chainlit as cl
from init_setup import ChainlitEnv
from chainlit.input_widget import Switch, TextInput 
from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
)
from metagpt.team import Team


# https://docs.chainlit.io/concepts/starters
@cl.set_chat_profiles
async def chat_profile() -> list[cl.ChatProfile]:
    """Generates a chat profile containing starter messages which can be triggered to run MetaGPT

    Returns:
        list[chainlit.ChatProfile]: List of Chat Profile
    """
    return [
        cl.ChatProfile(
            name="MetaGPT",
            icon="/public/MetaGPT-new-log.jpg",
            markdown_description="It takes a **one line requirement** as input and outputs **user stories / competitive analysis / requirements / data structures / APIs / documents, etc.**, But `everything in UI`.",
            starters=[
                cl.Starter(
                    label="Create a 2048 Game",
                    message="Create a 2048 game",
                    icon="/public/2048.jpg",
                ),
                cl.Starter(
                    label="Write a cli Blackjack Game",
                    message="Write a cli Blackjack Game",
                    icon="/public/blackjack.jpg",
                ),
            ],
        )
    ]

@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings(
        [
            TextInput(id="ProjectName", label="Project Name"),
            TextInput(id="ProjectPath", label="Project Path"),
            Switch(id="Incremental", label="Incremental Feature"),
        ]
    ).send()
@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set('incremental', settings['Incremental'])
    cl.user_session.set('project_path', settings['ProjectPath'])
    cl.user_session.set('project_name', settings['ProjectName'])
# https://docs.chainlit.io/concepts/message
@cl.on_message
async def startup(message: cl.Message) -> None:
    """On Message in UI, Create a MetaGPT software company

    Args:
        message (chainlit.Message): message by chainlist
    """
    idea = message.content
    company = Team(env=ChainlitEnv())

    # Similar to software_company.py
    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
            Engineer(n_borg=5, use_code_review=True),
            QaEngineer(),
        ]
    )
    company.env.context.config.inc = cl.user_session.get('incremental')
    company.env.context.config.project_path = cl.user_session.get('project_path')
    company.env.context.config.project_name = cl.user_session.get('project_name')
    company.invest(investment=3.0)
    company.run_project(idea=idea)

    await company.run(n_round=5)

    workdir = company.env.context.git_repo.workdir
    files = company.env.context.git_repo.get_files(workdir)
    files = "\n".join([f"{workdir}/{file}" for file in files if not file.startswith(".git")])

    await cl.Message(
        content=f"""
Codes can be found here:
{files}

---

Total cost: `{company.cost_manager.total_cost}`
"""
    ).send()
