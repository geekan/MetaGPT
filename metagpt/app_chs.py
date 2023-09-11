#!/usr/bin/env python
# -*- coding: utf-8 -*-

import aiofiles
import gradio as gr 
from metagpt.software_company import SoftwareCompany, SoftwareCompanyWithHuman
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

async def startup(company_name : str,
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

    if company_name == "软件公司":
        company = SoftwareCompany()
    elif company_name == "可以人为干预的软件公司":
        company = SoftwareCompanyWithHuman()
    else:
        return "不支持的公司类型"
    if idea == "":
        return "请输入你的创意"
    staff_list = []
    for staff in staffs:
        if staff == "项目经理":
            staff_list.append(ProjectManager())
        elif staff == "产品经理":
            staff_list.append(ProductManager())
        elif staff == "架构师":
            staff_list.append(Architect())
        else:
            raise Exception("不支持的员工类型")
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
    if company_name == "软件公司":
        await company.run(n_round)
    elif company_name == "可以人为干预的软件公司":
        await company.continue_run()
    return "角色: "+company.environment.short_term_history.role, "行为: "+str(company.environment.short_term_history.cause_by),company.environment.short_term_history.sent_from,company.environment.short_term_history.send_to, company.environment.short_term_history.content, company.environment.short_term_history.content

async def __continue(message_content : str):
    company = SoftwareCompany_Company
    company.environment.short_term_history.content = message_content
    print(company.environment.short_term_history.content)
    company.environment.memory.add(company.environment.short_term_history)
    company.environment.history += f"\n{company.environment.short_term_history}"
    await company.continue_run()
    return "角色: "+company.environment.short_term_history.role, "行为: "+str(company.environment.short_term_history.cause_by),company.environment.short_term_history.sent_from,company.environment.short_term_history.send_to, company.environment.short_term_history.content, company.environment.short_term_history.content

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
            company_choise = gr.Dropdown(label = "选择公司类型", choices = ["软件公司", "可以人为干预的软件公司"], value = "可以人为干预的软件公司")
            with gr.Row():
                investment = gr.Slider(minimum=0.0, maximum=20.0, step=0.1, label="投资",value = 6.0, info="The maxmium money you want to spend on the GPT generation")
                n_round = gr.Number( label="轮数", value = 5, info="你想要运行的最大轮数",visible = False)
            with gr.Row():
                run_tests = gr.Checkbox(label = "是否要雇佣质量保证工程师来进行测试", value = False)
                with gr.Row():
                    implement = gr.Checkbox(label = "是否要雇佣工程师来实施项目(仅支持python)", value = True)
                    code_review = gr.Checkbox(label = "是否进行代码检查", value = False)
            staffs = gr.CheckboxGroup(["项目经理", "产品经理", "架构师"], label="Choose the staff you would like to hire", value = ["项目经理", "产品经理", "架构师"])
            idea = gr.Textbox(label="你的创新想法，比如：“做一个贪吃蛇游戏”", value = "做一个贪吃蛇游戏")
            with gr.Row():
                Start_MetaGPT = gr.Button(label="开始 / 重新开始", value = "开始 / 重新开始")
                continue_run = gr.Button(label="继续", value = "继续", visible = True)
            with gr.Row():
                show_markdown = gr.Checkbox(label="展示Markdown")
            # with gr.Row():
            #     clear_log = gr.Button(label="Clear Log", value = "Clear Log") # temporary, should be removed in the future
            notice_metagpt = gr.Markdown(value = "每轮生成时间大约为45秒，请耐心等待")
            with gr.Row():
                output_role_metagpt = gr.Markdown(label="角色")
                output_cause_metagpt = gr.Markdown(label="行为")
            with gr.Row():
                output_sent_from_metagpt = gr.Markdown(label="发送者")
                output_send_to_metagpt = gr.Markdown(label="接收者")

            with gr.Row():
                output_content_metagpt = gr.Textbox(label="MetaGPT的阶段性输出,按照你的意愿进行修改",max_lines=999,show_copy_button = True)
                output_content_markdown_metagpt = gr.Markdown(label="Markdown输出", visible = False)
            
            
        Start_MetaGPT.click(startup, [company_choise, idea, investment, n_round, code_review, run_tests, implement, staffs], [output_role_metagpt,output_cause_metagpt,output_sent_from_metagpt,output_send_to_metagpt,output_content_metagpt,output_content_markdown_metagpt])
        # clear_log.click(clear_logs, [],[])
        continue_run.click(__continue, [output_content_metagpt], [output_role_metagpt,output_cause_metagpt,output_sent_from_metagpt,output_send_to_metagpt,output_content_metagpt,output_content_markdown_metagpt])
        company_choise.change(lambda company_choise : gr.update(visible = True if company_choise == "可以人为干预的软件公司" else False), [company_choise], [continue_run])
        company_choise.change(lambda company_choise : gr.update(visible = False if company_choise == "可以人为干预的软件公司" else True), [company_choise], [n_round])
        show_markdown.change(lambda x: gr.update(visible = True if x == True else False), [show_markdown], [output_content_markdown_metagpt])
        with gr.TabItem("Research") as research_tab:
            language = gr.Dropdown(label = "Choose the language", choices = ["en-us","zh-ch"], value = "en-us")
            topic = gr.Textbox(label="Your research topic, such as 'dataiku vs. datarobot'", value = "dataiku vs. datarobot")
            submit_Research = gr.Button(label="Submit", value = "Submit")
            output_path_md = gr.Textbox(label="Output")
        submit_Research.click(research_startup, [language,topic], outputs=[output_path_md])

if __name__ == "__main__":
    app.queue(concurrency_count=1022, max_size=2044).launch(inbrowser=True)