#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/19 17:12
@Author  : ORI_Replication
@File    : app.py
"""
import gradio as gr 
from metagpt.software_company import SoftwareCompany
from metagpt.roles import ProjectManager,ProductManager, Architect,Engineer, QaEngineer
from metagpt.roles.researcher import RESEARCH_PATH, Researcher


class Report:
  def __init__(self, role, action, sent_from, send_to, content):
    self.role = role
    self.action = action 
    self.sent_from = sent_from
    self.send_to = send_to
    self.content = content

async def startup(company_name : str,
                      idea : str,
                      staffs : list,
                      investment : float = 6.0,
                      n_round : int = 5,
                      code_review : bool = False,
                      auto_mode : bool = False,
                      ):
    global SoftwareCompany_Company
    
    if company_name == "SoftwareCompany": company = SoftwareCompany()
    else: return "Company type not supported"
    if idea == "": return "Please input your idea"
    staff_list = []
    for staff in staffs:
        if staff == "ProjectManager": staff_list.append(ProjectManager())
        elif staff == "ProductManager": staff_list.append(ProductManager())
        elif staff == "Architect": staff_list.append(Architect())
        elif staff == "Engineer": staff_list.append(Engineer(n_borg=5,use_code_review=code_review))
        elif staff == "QaEngineer": staff_list.append(QaEngineer())
    company.hire(staff_list)
    company.invest(investment)
    company.start_project(idea)
    # report all output to webui
    SoftwareCompany_Company = company
    if auto_mode:
        company.environment.human_interaction = False
        await company.run(n_round)
    else :
        company.environment.human_interaction = True
    report = Report(company.environment.short_term_history.role,
                        str(company.environment.short_term_history.cause_by),
                        company.environment.short_term_history.sent_from,
                        company.environment.short_term_history.send_to,
                        company.environment.short_term_history.content)
    return report.role, report.action, report.sent_from, report.send_to, report.content, report.content

async def __continue(message_content : str):
    company = SoftwareCompany_Company
    company.environment.short_term_history.content = message_content
    company.environment.memory.add(company.environment.short_term_history)
    company.environment.history += f"\n{company.environment.short_term_history}"
    await company.run_one_round()
    report = Report(company.environment.short_term_history.role,
                        str(company.environment.short_term_history.cause_by),
                        company.environment.short_term_history.sent_from,
                        company.environment.short_term_history.send_to,
                        company.environment.short_term_history.content)
    return report.role, report.action, report.sent_from, report.send_to, report.content, report.content

async def research_startup(language : str, topic : str):
    role = Researcher(language="en-us")
    await role.run(topic)
    return f"save report to {RESEARCH_PATH / f'{topic}.md'}."

    
app = gr.Blocks()
SoftwareCompany_Company = SoftwareCompany()

with app:
    gr.Markdown("""
                # MetaGPT
                """)
    
    with gr.Tabs():
        with gr.TabItem("MetaGPT") as generate_tab: 
            company_choise = gr.Dropdown(label = "Choose the company type",choices = ["SoftwareCompany"],value = "SoftwareCompany")
            with gr.Row():
                investment = gr.Slider(minimum=0.0, maximum=20.0, step=0.1, label="Investment",value = 6.0,\
                                        info="The maxmium money you want to spend on the GPT generation")
                n_round = gr.Number( label="Round", value = 5, info="The maxmium round you want to run",visible = True)
            with gr.Row():
                code_review = gr.Checkbox(label = "Whether to use code review", value = False)
                auto_mode = gr.Checkbox(label = "Whether to use auto mode", info = "run without human interaction", value = False)
            staffs = gr.CheckboxGroup(["ProjectManager", "ProductManager", "Architect", "Engineer", "QaEngineer"],\
                                        label="Choose the staff you would like to hire",\
                                        value = ["ProjectManager", "ProductManager", "Architect", "Engineer"])
            idea = gr.Textbox(label="Your innovative idea, such as 'Creating a snake game.'", value = "Creating a snake game.")
            with gr.Row():
                Start_MetaGPT = gr.Button(label="Start / ReStart", value = "Start / ReStart")
                continue_run = gr.Button(label="Continue Run", value = "Continue Run", visible = True)
            with gr.Row():
                show_markdown = gr.Checkbox(label="Show Markdown")
            # with gr.Row():
            #     clear_log = gr.Button(label="Clear Log", value = "Clear Log") # temporary, should be removed in the future
            with gr.Row():
                output_role_metagpt = gr.Markdown(label="The role of the output of MetaGPT")
                output_cause_metagpt = gr.Markdown(label="The cause of the output of MetaGPT")
            with gr.Row():
                output_sent_from_metagpt = gr.Markdown(label="The sent_from of the output of MetaGPT")
                output_send_to_metagpt = gr.Markdown(label="The send_to of the output of MetaGPT")
            with gr.Row():
                output_content_metagpt = gr.Textbox(label="The phased output of MetaGPT, modify it as your will",\
                                                    max_lines=999,show_copy_button = True)
                output_content_markdown_metagpt = gr.Markdown(label="The markdown output of MetaGPT", visible = False)
              
        Start_MetaGPT.click(startup, [company_choise, idea, staffs, investment, n_round, code_review, auto_mode],\
            [output_role_metagpt,output_cause_metagpt,output_sent_from_metagpt,output_send_to_metagpt,\
            output_content_metagpt,output_content_markdown_metagpt])
        # clear_log.click(clear_logs, [],[])
        continue_run.click(__continue, [output_content_metagpt],\
            [output_role_metagpt,output_cause_metagpt,output_sent_from_metagpt,output_send_to_metagpt,\
            output_content_metagpt,output_content_markdown_metagpt])
        company_choise.change(lambda company_choise : gr.update(visible = True \
            if company_choise == "SoftwareCompany_With_Human" else False), [company_choise], [continue_run])
        company_choise.change(lambda company_choise : gr.update(visible = False \
            if company_choise == "SoftwareCompany_With_Human" else True), [company_choise], [n_round])
        show_markdown.change(lambda x: gr.update(visible = True if x == True else False),\
            [show_markdown], [output_content_markdown_metagpt])
        
        with gr.TabItem("Research") as research_tab:
            language = gr.Dropdown(label = "Choose the language", choices = ["en-us","zh-ch"], value = "en-us")
            topic = gr.Textbox(label="Your research topic, such as 'dataiku vs. datarobot'", value = "dataiku vs. datarobot")
            submit_Research = gr.Button(label="Submit", value = "Submit")
            output_path_md = gr.Textbox(label="Output")
        submit_Research.click(research_startup, [language,topic], outputs=[output_path_md])

if __name__ == "__main__":
    app.queue(concurrency_count=1022, max_size=2044).launch(inbrowser=True)