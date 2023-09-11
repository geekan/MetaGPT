#!/usr/bin/env python
# -*- coding: utf-8 -*-

import aiofiles
import gradio as gr 
from metagpt.software_company import SoftwareCompany
from metagpt.roles import ProjectManager, ProductManager, Architect, Engineer, QaEngineer, Searcher, Sales, customer_service
from metagpt.roles.researcher import RESEARCH_PATH, Researcher
import io
import asyncio
import threading
from metagpt.const import PROJECT_ROOT
from time import sleep
from metagpt.schema import Message
import sys



def clear_logs():
    with open(PROJECT_ROOT / 'logs/log.txt', 'w') as f:
        f.write("")

async def startup(company : str,
                      idea : str,
                      investment : float = 6.0,
                      n_round : int = 5,
                      code_review : bool = True,
                      run_tests : bool = False,
                      implement : bool = True,
                      staffs : list = ["ProjectManager",
                                      "ProductManager",
                                      "Architect",]
                      )->SoftwareCompany:

    if company == "SoftwareCompany":
        company = SoftwareCompany()
    else:
        raise Exception("Company type not supported")
    if idea == "":
        raise Exception("Please input your idea")
    staff_list = []
    for staff in staffs:
        if staff == "ProjectManager":
            staff_list.append(ProjectManager())
        elif staff == "ProductManager":
            staff_list.append(ProductManager())
        elif staff == "Architect":
            staff_list.append(Architect())
        else:
            raise Exception("Staff type not supported")
    company.hire(staff_list)
        # if implement or code_review
    if implement or code_review:
        # developing features: implement the idea
        company.hire([Engineer(n_borg=5, use_code_review=code_review)])

    if run_tests:
        # developing features: run tests on the spot and identify bugs
        # (bug fixing capability comes soon!)
        company.hire([QaEngineer()])
    company.invest(investment)
    company.start_project(idea)
    # report all output to webui
    global SoftwareCompany_Company
    SoftwareCompany_Company = company
    await company.continue_run()
    return company.environment.short_term_history.content

async def __continue(message_content : str):
    company = SoftwareCompany_Company
    company.environment.short_term_history.content = message_content
    print(company.environment.short_term_history.content)
    company.environment.memory.add(company.environment.short_term_history)
    company.environment.history += f"\n{company.environment.short_term_history}"
    await company.continue_run()
    return company.environment.short_term_history.content

async def research_startup(language : str,
                           topic : str):
    if language == "en-us":
        language = "en-us"
    elif language == "zh-ch":
        language = "zh-ch"
    else:
        raise Exception("Language not supported")
    role = Researcher(language="en-us")
    await role.run(topic)
    return f"save report to {RESEARCH_PATH / f'{topic}.md'}."

app = gr.Blocks()
SoftwareCompany_Company = SoftwareCompany()
import sys
sys.path.append('/workspaces/CSworks/zknow/proj_meta_gpt_linux/metagpt/metagpt')
with app:
    gr.Markdown("""
                # MetaGPT
                """)
    with gr.Tabs():
        with gr.TabItem("MetaGPT") as generate_tab:
            company_choise = gr.Dropdown(label = "Choose the company type", choices = ["SoftwareCompany"], value = "SoftwareCompany")
            with gr.Row():
                investment = gr.Slider(minimum=0.0, maximum=20.0, step=0.1, label="The maxmium money($) you would like to spend on generate",value = 6.0)
                n_round = gr.Number( label="Round", value = 5)
            with gr.Row():
                run_tests = gr.Checkbox(label = "Whether to hire a QaEngineer to run tests", value = False)
                with gr.Row():
                    implement = gr.Checkbox(label = "Whether to hire a Engineer to implement the idea(write code)", value = True)
                    code_review = gr.Checkbox(label = "Whether to use code review", value = False)
            staffs = gr.CheckboxGroup(["ProjectManager", "ProductManager", "Architect"], label="Choose the staff you would like to hire", value = ["ProjectManager", "ProductManager", "Architect"])
            idea = gr.Textbox(label="Your innovative idea, such as 'Creating a snake game.'", value = "Creating a snake game.")
            with gr.Row():
                Start_MetaGPT = gr.Button(label="Start", value = "Start")
            with gr.Row():
                clear_log = gr.Button(label="Clear Log", value = "Clear Log") # temporary, should be removed in the future
            output_metagpt = gr.Textbox(label="The phased output of MetaGPT, modify it as your will",max_lines=999,show_copy_button = True)
            continue_run = gr.Button(label="Continue Run", value = "Continue Run")
        Start_MetaGPT.click(startup, [company_choise, idea, investment, n_round, code_review, run_tests, implement, staffs], [output_metagpt])
        clear_log.click(clear_logs, [],[])
        continue_run.click(__continue, [output_metagpt], [output_metagpt])
        with gr.TabItem("Research") as research_tab:
            language = gr.Dropdown(label = "Choose the language", choices = ["en-us","zh-ch"], value = "en-us")
            topic = gr.Textbox(label="Your research topic, such as 'dataiku vs. datarobot'", value = "dataiku vs. datarobot")
            submit_Research = gr.Button(label="Submit", value = "Submit")
            output_path_md = gr.Textbox(label="Output")
        submit_Research.click(research_startup, [language,topic], outputs=[output_path_md])


if __name__ == "__main__":
    app.queue(concurrency_count=1022, max_size=2044).launch(inbrowser=True)