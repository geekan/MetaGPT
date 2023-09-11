import gradio as gr 
from metagpt.software_company import SoftwareCompany
from metagpt.roles import ProjectManager, ProductManager, Architect, Engineer, QaEngineer, Searcher, Sales, CustomerService
import io
import asyncio
import threading


log_stream = io.StringIO()

async def report_logs(interface: gr.Interface):
    """report logs to webui"""
    print("report_logs\n\n\n\n\n")
    while True:
        #if there are new logs, report them
        if log_stream.getvalue() != "":
            interface.outputs[0].textbox.value = log_stream.getvalue()
            log_stream.truncate(0)
            log_stream.seek(0)
        await asyncio.sleep(0.1)    

async def startup(company : str,
                      idea : str,
                      investment : float = 6.0,
                      n_round : int = 5,
                      code_review : bool = True,
                      run_tests : bool = False,
                      implement : bool = True,
                      staffs : list = ["ProjectManager",
                                      "ProductManager",
                                      "Architect",
                                      "Engineer"]):
    """create a webui with gradio"""
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
    asyncio.gather(
        report_logs(demo),
        company.run(n_round = n_round)
        )
    

    
        
    
demo = gr.Interface(fn=startup, 
                    inputs=[
                        gr.Dropdown(["SoftwareCompany"],label="Company", info="Choose the company type"),
                        gr.Textbox(label="Idea", info="Your innovative idea, such as 'Creating a snake game.'"),
                        gr.Slider(minimum=0.0, maximum=20.0, step=0.1, label="Investment", info="The maxmium money($) you would like to spend on generate"),
                        gr.Number( label="Round", info="The maxmium round you would like to run"),
                        gr.Checkbox(label="Code Review", info="Whether to use code review"),
                        gr.Checkbox(label="Run Tests", info="Whether to hire a QaEngineer to run tests"),
                        gr.Checkbox(label="Implement", info="Whether to hire a Engineer to implement the idea(write code)"),
                        gr.CheckboxGroup(["ProjectManager", "ProductManager", "Architect"], label="Staff", info="Choose the staff you would like to hire")
                        ],
                    outputs=[
                        gr.Textbox(label="Output", type="text", default=""),
                        ],
                    title="AI Startup",
                    examples=[
                        ["SoftwareCompany", "Creating a snake game.", 6.0, 5, True, False, True, ["ProjectManager", "ProductManager", "Architect"]],
                    ]
)

if __name__ == "__main__":
    demo.launch()