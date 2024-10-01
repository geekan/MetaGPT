import gradio as gr
import json,os ,shutil
from typing import Optional
from pathlib import Path
from pydantic import Field
from metagpt.const import DATA_PATH
from metagpt.schema import Message, Plan
from metagpt.actions import SearchAndSummarize, UserRequirement 
from metagpt.ext.ai_writer.write_planner import DocumentPlan, WritePlanner
from metagpt.ext.ai_writer.write_refine import WriteGuide,Refine,WriteSubsection,Clean
from metagpt.ext.ai_writer.document import build_engine
from metagpt.ext.ai_writer.utils import  WriteOutFile

class DocumentGenerator(WritePlanner):
    """
    继承自WritePlanner的类,用于生成文档。
    """
    store: Optional[object] = Field(default=None, exclude=True) 
    def  add_file_button(self, topic, history, add_file_button):
            ref_dir =     DATA_PATH / f"ai_writer/ref/{topic}"
            persist_dir = DATA_PATH / f"persist/{topic}"
            
            if  not os.path.isdir(ref_dir):
                os.makedirs(ref_dir)
            for file in add_file_button:
                shutil.move(file, ref_dir)
                history.append(('完成解析', file))  
                
            model ='model/bge-large-zh-v1.5'
            self.store = build_engine(ref_dir,persist_dir,model)
            shutil.rmtree(ref_dir)  
            return history

    async def generate_outline(self):
        """
        异步生成文档大纲。
        """
        context = self.get_useful_memories()
        response = await DocumentPlan().run(context)
        self.working_memory.add(Message(content=response, role="assistant", cause_by=DocumentPlan))
        return response
    
    async def gen_outline_button(self, requirements):
            self.plan = Plan(goal=requirements.strip())
            response = await self.generate_outline()
            return [(requirements, response)]
    

    async def submit_outline_button(self, user_input, conversation_history):
            self.working_memory.add(Message(content=user_input, role="user"))
            response =  await self.generate_outline()
            conversation_history.append((user_input, response))
            return "Outline updated", conversation_history
        
    def confirm_outline_button(self, requirements, history, outline):
        self.plan = Plan(goal=requirements.strip())
        if  not outline:
            outline = history[-1][-1] if history  else ''
        '''根据大纲建文档目录树状结构'''
        rsp = self.post_process_chapter_id_or_name(outline)
        self.titlehierarchy = self.process_response_and_build_hierarchy(rsp=rsp)   
        return outline
    
    
    def get_name_and_subheading(self,id):
        obj  =  self.titlehierarchy.get_chapter_obj_by_id(id)
        chapter_name  = obj.name 
        subheadings = self.titlehierarchy.get_subheadings_by_prefix(id)
        return chapter_name, '\n'.join(subheadings) 
    
    async def retrieve_button(self,chapter_name):
        contexts = '请上传关联文件'
        if self.store:
            contexts = await self.store.aretrieve(chapter_name)
            contexts = '\n\n'.join([x.text for x in contexts]) 
        return contexts
    
    async def retrieve_clean(self,title, contexts):
        context = ''
        if self.store:
            context =  await Clean().run(title = title, contexts = contexts) 
        return context
    
    
    
    async def gen_guide(self, chapter_id, chapter_name, subheadings, history):
        if  subheadings:
            contexts = await self.retrieve_button(chapter_name)
            guideline = await WriteGuide().run(
                                    user_requirement= self.plan.goal,
                                    chapter_name = chapter_name,
                                    subheadings = ','.join([section for section in subheadings]),
                                    contexts =  contexts
                                )
            history.append((f'{chapter_id} {chapter_name}', guideline))
            self.titlehierarchy.set_content_by_id(chapter_id, guideline)
            yield  history 
            
            for subheading in subheadings:
                chapter_id, name = subheading.split(' ')
                subtitle = self.titlehierarchy.get_subheadings_by_prefix(chapter_id)    
                async for output in self.gen_guide(chapter_id, name, subtitle, history):
                      yield output 
                      
    async def gen_guide_button(self, chapter_id, history):
        history = []
        subheadings = self.titlehierarchy.get_subheadings_by_prefix(chapter_id)
        chapter_name = self.titlehierarchy.get_chapter_obj_by_id(chapter_id).name
        async   for output in self.gen_guide(chapter_id, chapter_name, subheadings, history):
                    yield output 
     
    async def write_paragraph(self, parent_id, child_id, chapter_name, subheadings, history):
        if  subheadings:
            guidelines = self.titlehierarchy.get_chapter_obj_by_id(parent_id).content
            history.append((f'{child_id} {chapter_name}', guidelines))
            yield  history 
            
            for subheading in subheadings:
                child_id, chapter_name = subheading.split(' ')
                child_heading = self.titlehierarchy.get_subheadings_by_prefix(child_id)    
                async for output in self.write_paragraph(parent_id, child_id, chapter_name, child_heading, history):
                      yield output 
        else:
            contexts = await self.retrieve_button(chapter_name)
            guidelines =  self.titlehierarchy.get_chapter_obj_by_id(parent_id).content
            gen_paragraph = await WriteSubsection().run(
                            subsection = chapter_name,
                            contexts = f'{guidelines}\n\n# Reference: \n```{contexts}```'
                )
            history.append((f'{child_id} {chapter_name}', gen_paragraph))
            yield  history 
       
       
    async def write_paragraph_button(self, chapter_id, history):
            history = []
            subheadings = self.titlehierarchy.get_subheadings_by_prefix(chapter_id)
            chapter_name = self.titlehierarchy.get_chapter_obj_by_id(chapter_id).name
            async   for output in self.write_paragraph(chapter_id, chapter_id, chapter_name, subheadings, history):
                    yield output     
    
            
            
    async def refine_button(self, revise_id, instrution, addition_context, revise_text):
            obj =  self.titlehierarchy.get_chapter_obj_by_id(revise_id.lstrip())
            chapter_name , pre_result = obj.name , obj.content
            cur_result = await Refine().run(
                                            user_requirement = instrution,
                                            original_query = chapter_name,
                                            respones = '\n\n'.join([pre_result, revise_text]) ,
                                            contexts = addition_context 
                                            )
            return  cur_result 
     
    async def web_button(self, revise_id, instrution): 
            chapter_name = self.titlehierarchy.get_chapter_obj_by_id(revise_id.lstrip()).name
            prompt = instrution if instrution else chapter_name
            message = [Message(content= prompt, role="user", cause_by = UserRequirement)]  
            addition_context = await SearchAndSummarize().run(message)     
            return addition_context
             
    def commit_button(self, revise_id, revise_text, chatbot):
        self.titlehierarchy.set_content_by_id(revise_id, revise_text)
        new_chatbot = []
        for title, content in chatbot:
            cur_id, _ = title.split(' ')
            if  cur_id == revise_id:
                new_chatbot.append((title, revise_text))    
            else:
                new_chatbot.append((title, content))    
        return new_chatbot 
    
    def download_button(self,topic):
        output_path = DATA_PATH / f"ai_writer/outputs/{topic}.docx"
        if  not output_path.exists():
            
            WriteOutFile.write_word_file(topic = topic, 
                                        tasks= self.titlehierarchy.traverse_and_output(),
                                        output_path = output_path
                                        )
            
        return gr.DownloadButton(label=f"Download", value= output_path, visible=True) 
    
    @staticmethod                    
    def create_directory_structure_botton(data, prefix="", is_last=True):
        data = json.loads(data)
        chatbot = ''
        for index, item in enumerate(data):
            chapter_name = item["chapter_name"]
            subheadings = item.get("subheadings", [])
            # Determine the prefix based on whether it's the last item in its level
            current_prefix = f"{prefix}{'└── ' if is_last else '├── '}"
            # Print the main directory
            chatbot += (f"{current_prefix}{chapter_name}\n")
            # Update the prefix for subdirectories
            next_prefix = f"{prefix}{'    ' if is_last else '│   '}"
            # If there are subheadings, handle them differently to ensure correct indentation
            if subheadings:
                chatbot += (f"{next_prefix}├──\n")
                for sub_index, subheading in enumerate(subheadings):
                    sub_current_prefix = f"{next_prefix}{'    ' if sub_index == len(subheadings) - 1 else '│   '}"
                    chatbot += (f"{sub_current_prefix}├── {subheading}\n")
        return  [('',chatbot)]      


doc_gen = DocumentGenerator()

async def main():
    with gr.Blocks(css="") as demo:
        gr.Markdown("## AI 智能文档写作 Demo")
        with gr.Row():
            with gr.Column(scale=0, elem_id="row1"):
                with gr.Tab("开始"):
                    topic = gr.Textbox(
                        "产业数字化对中国出口隐含碳的影响",
                        label="话题",
                        lines=7,
                        interactive=True,
                        )
                    user_requriments = gr.Textbox(
                        "写一个完整、连贯的《产业数字化对中国出口隐含碳的影响》文档, 确保文字精确、逻辑清晰，并保持专业和客观的写作风格，中文书写",
                        label="用户需求",
                        lines=9,
                        interactive=True,
                        )
                    add_file_button = gr.UploadButton("📁 Upload (上传文件)",file_count="multiple")
                    gen_outline_button = gr.Button("生成大纲")
                    
    
                with gr.Tab("大纲"):
                    outline_box = gr.Textbox(label="大纲", 
                                            lines=16, 
                                            interactive=True)
                    
                    user_input  = gr.Textbox('eg:请帮我新增章节',
                                             lines=2, 
                                             label='大纲修订(增删改)')
                    submit_outline_button = gr.Button("提交")
                    confirm_outline_button = gr.Button("确认")

                    
                with gr.Tab("生成段落"):
                    chapter_id = gr.Textbox('1',label="chapter_id", lines=1, interactive=True)
                    chapter_name = gr.Textbox('',label="大章节名称", lines = 1, interactive=False)
                    chapter_subname =  gr.Textbox('',label="小节名称", lines=2, interactive=False) 
                    retrieve_bot =  gr.Textbox('',label="资源检索", lines=5, interactive=False) 
                    retrieve_button = gr.Button("资源检索")
                    gen_guide_button = gr.Button("生成指南")
                    write_paragraph_button = gr.Button("生成段落")
                    
                    
                with gr.Tab("功能区"):
                    instrution = gr.Textbox(label="润色指令", lines=4, interactive=True)
                    addition_context = gr.Textbox(label="临时新增内容", lines=10, interactive=True)
                    refine_button = gr.Button("润色")
                    web_button = gr.Button("联网") 
                    download_button = gr.DownloadButton("下载",
                                                        visible=True,) 
                    
            with gr.Column(scale=3, elem_id="row2"):
                chatbot = gr.Chatbot(label='output', height=690)
                
            with gr.Column(scale=0, elem_id="row3"):
                revise_text = gr.Textbox(
                    label="修订", lines=30, interactive=True, show_copy_button=True
                )
                commit_button = gr.Button("确认")
             
            add_file_button.upload(doc_gen.add_file_button,
                                        inputs=[topic, chatbot, add_file_button],
                                        outputs = [chatbot],
                                        show_progress = True
                                ) 
                
                
            gen_outline_button.click(doc_gen.gen_outline_button,
                                        inputs=[user_requriments],
                                        outputs=[chatbot],
                                        show_progress = True
                                    )
            
            submit_outline_button.click(
                                        doc_gen.submit_outline_button,
                                        inputs=[user_input, chatbot],  
                                        outputs=[user_input, chatbot]  
                                    )
            
            
            confirm_outline_button.click(
                                        doc_gen.confirm_outline_button,
                                        inputs=[user_requriments, chatbot, outline_box],
                                        outputs=[outline_box] 
                                    ).then(
                                        doc_gen.create_directory_structure_botton,
                                        inputs=[outline_box],
                                        outputs=[chatbot] 
                                    )
                                    
            retrieve_button.click(
                    doc_gen.get_name_and_subheading,
                    inputs = [chapter_id],
                    outputs= [chapter_name,chapter_subname]
                    ).then(
                    doc_gen.retrieve_button,
                    inputs = [chapter_name],  
                    outputs= [retrieve_bot]  
                    ).then(
                    doc_gen.retrieve_clean,
                    inputs = [chapter_name,retrieve_bot],  
                    outputs= [revise_text]
                    )      
                
                
            gen_guide_button.click(
                    doc_gen.get_name_and_subheading,
                    inputs = [chapter_id],
                    outputs= [chapter_name,chapter_subname]
                    ).then(
                    doc_gen.gen_guide_button,
                    inputs=[chapter_id, chatbot],  
                    outputs=[chatbot]  
                    )
                     
            write_paragraph_button.click(
                    doc_gen.write_paragraph_button,
                    inputs=[chapter_id, chatbot],  
                    outputs=[chatbot]  
                )
            
            refine_button.click(doc_gen.refine_button,
                       inputs= [chapter_id, instrution,addition_context,revise_text],               
                       outputs=[revise_text],
                       show_progress = True              
                )    
                   
            web_button.click(doc_gen.web_button,
                       inputs= [chapter_id, instrution],               
                       outputs=[addition_context],
                       show_progress = True              
                )  
                              
            commit_button.click(doc_gen.commit_button,
                                inputs=[chapter_id, revise_text, chatbot],
                                outputs=[chatbot]
                                )   
            
            
            download_button.click(
                        doc_gen.download_button,
                        inputs=[topic],
                        outputs=download_button,
                        show_progress = True
                        )
            
   
    demo.queue().launch(
        share=True,
        inbrowser=False,
        server_port=8888,
        server_name="0.0.0.0"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
