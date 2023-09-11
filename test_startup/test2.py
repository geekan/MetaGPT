from time import sleep
import aiofiles
import gradio as gr 
from metagpt.software_company import SoftwareCompany
from metagpt.roles import ProjectManager, ProductManager, Architect, Engineer, QaEngineer, Searcher, Sales, CustomerService
import io
import asyncio
import threading
from metagpt.const import PROJECT_ROOT

def report_logs():
    while True:
        with open(PROJECT_ROOT / 'logs/log.txt', 'r') as f:

            print(f.read())
            sleep(1)
            
print(PROJECT_ROOT)