from __future__ import annotations
from typing import Literal,List, Optional
import re
from pydantic import Field, model_validator
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.tools.search_engine import SearchEngine
from metagpt.schema import Message, Task, TaskResult
from llama_index.core import  Document
from metagpt.ext.ai_writer.write_refine import WriteGuide,Refine, WriteSubsection, Clean
from metagpt.actions import SearchAndSummarize, UserRequirement 
from metagpt.ext.ai_writer.write_planner import WritePlanner
from metagpt.ext.ai_writer.utils import colored_decorator, print_time


class DocumentWriter(Role):
    name: str = "wangs"
    profile: str = "document_writer"
    goal: str = "write a long document"
    auto_run: bool = True
    use_plan: bool = True
    react_mode: Literal["plan_and_act", "react"] =  'plan_and_act'    #"by_order"
    human_design_planner: bool = False
    max_react_loop : int = 5
    planner: WritePlanner = Field(default_factory= WritePlanner)
    use_store:bool = True
    store: Optional[object] = Field(default=None, exclude=True) 
    store_mode: Literal["search", "retrieve", "retrieve_clean"] = "retrieve_clean"  
    
    
    @model_validator(mode="after")
    def set_plan(self):
        self._set_react_mode(react_mode=self.react_mode, max_react_loop=self.max_react_loop, auto_run=self.auto_run)
        self.planner = WritePlanner(auto_run=self.auto_run,
                                    human_design_planner = self.human_design_planner
                                    )
        
        self.use_plan = (self.react_mode == "plan_and_act" )      
        self.set_actions([WriteGuide, Refine, WriteSubsection])
        self._set_state(0)
        return self
    
    @model_validator(mode="after")
    def validate_stroe(self):
        if self.store:
            search_engine = SearchEngine.from_search_func(search_func=self.store.asearch, proxy=self.config.proxy)
            action = SearchAndSummarize(search_engine=search_engine, context=self.context)
        else:
            action = SearchAndSummarize(context=self.context)
        self.actions.append(action)    
        return self
    
    @property
    def working_memory(self):
        return self.rc.working_memory
    
    @print_time
    async def run(self, requirement) -> Message | None:
        return await super().run(requirement)
        
    async def _act_on_task(self, current_task: Task) -> TaskResult:
        """
        Process a given task by either writing an initial draft or refining a draft based on user feedback .
        This method differentiates the action to be taken based on the completion status of the task.
        If the task is marked as finished, it will refine the draft; otherwise, it will write a new draft.
        """
        id = re.sub(r'\.\d+', '', current_task.task_id)  
        chapter_name = current_task.instruction
        first_subheadings = self.planner.titlehierarchy.get_subheadings_by_prefix(id)
        
        if  not current_task.is_finished: 
            await self.write_draft(id,  chapter_name,  first_subheadings)
        else:
            await self.refine_draft()
          
        current_task.is_finished = True      
        task_result = TaskResult(
                                result = '',
                                is_success = True
                                )
        return task_result
    
    
    async def refine_draft(self):
        """
        Refine the draft based on user feedback associated with the task.
        """
        pass
    
    
    async def write_draft(self, id:str, chapter_name:str,  subheadings:List[str]):
        """
        this function is responsible for creating an initial draft of a chapter based on provided information.

        Parameters:
            - `id` (str): Unique identifier for the chapter.
            - `chapter_name` (str): The title of the chapter to be written.
            - `subheadings` (List[str]): A list of subheading titles for the chapter's content.  
        """
        if  subheadings:
            self._set_state(0)  
            guidelines, cause_by = await self.generate_guide(chapter_name,subheadings)
            self.working_memory.add(Message(content= guidelines, role="assistant", cause_by=cause_by))
            
            self._set_state(1)
            guidelines, cause_by = await self.refine_guide(chapter_name,guidelines)
            self.working_memory.add(Message(content= guidelines, role="assistant", cause_by=cause_by))
        else:
            subheadings, guidelines = [f"{id} {chapter_name}"], ''
            
        # No subheadings (subdirectories), no need to write guides, directly generated content.    
        self._set_state(2) 
        subheadings, gen_subsection, cause_by = await self.generate_parallel_subsection(subheadings,guidelines)
        self.working_memory.add_batch([Message(content = x, role="assistant", cause_by=cause_by) for x in gen_subsection]) 
        
        # Set guidelines and subsections into the heading hierarchy, an object used for document structure management.
        self.planner.titlehierarchy.set_content_by_id(id, guidelines)
        self.planner.titlehierarchy.set_content_by_headings(subheadings,gen_subsection)
       
        # Add the generated document to the node for easier retrieval
        await self.add_nodes_doc()
        # Log completion of actions
        logger.info(f"All actions for chapter {chapter_name} have been finished.")
    
    
    async def generate_guide(self, chapter_name:str,subheadings:List[str]):  
        """
        Generate the beginning guidelines of a chapter based on the current task and user requirements.
        This method initializes the generation process by checking for the existence of necessary
        attributes, retrieving user requirements, and context, then executing a task to generate
        the beginning of a document.
        
        Returns:
        tuple: A tuple containing the generated beginning of the chapter and the todo object used.
        """
        if  not hasattr(self, 'rc') or not hasattr(self.rc, 'todo'):
            raise AttributeError("Expected 'rc' and 'rc.todo' to be initialized") 
        
        todo = self.rc.todo  
        user_requirement = self.get_memories()[0].content
        logger.info("Starting to retrieve relevant information from documents")
        contexts = await self.doc_retrieve(chapter_name)
        logger.info("Starting to write the opening paragraph")
        guidelines = await todo.run(
                                    user_requirement=user_requirement,
                                    chapter_name = chapter_name,
                                    subheadings = ','.join([section for section in subheadings]),
                                    contexts = contexts
                                )
        return guidelines,  todo
    
    
    async def generate_parallel_subsection(self,subheadings,guidelines):  
        """
        Generate parallel subsections of a chapter concurrently based on the current task.
        This method generates multiple subsections of a chapter in parallel, using the task's
        dependent task IDs and the 'todo' object.
        It retrievescontexts for each subsection, and then runs the 'todo' task concurrently for each subsection.


        Returns:
        tuple: A tuple containing a list of results from the parallel tasks and the 'todo' object used.
        """
        
        if  not hasattr(self, 'rc') or not hasattr(self.rc, 'todo'):
            raise AttributeError("Expected 'rc' and 'rc.todo' to be initialized") 
        if  not isinstance(subheadings, list):
            subheadings =  [subheadings]
        
        todo = self.rc.todo  
        logger.info(f"ready to {todo.name}")
      
        context, first_headings = [], []
        for section in subheadings:
            _id, name = section.split(' ')
            subtitle = self.planner.titlehierarchy.get_subheadings_by_prefix(_id)
            if subtitle:
                await self.write_draft(_id, name,subtitle)
            else:
                contexts = await self.doc_retrieve(name)
                gen_subsection= await todo.run(
                                        subsection = section,
                                        contexts = f'{guidelines}\n\n# Reference: \n```{contexts}```'
                                        )
                first_headings.append(section)
                context.append(gen_subsection)
        # context = await asyncio.gather(*context)    
        return  first_headings, context , todo 

    
    async def refine_guide(self,chapter_name,guidelines): 
        """
        This method refines the beginning of a chapter by repeatedly asking for user review
        and instructions until the user confirms that the result is satisfactory.

        Returns:
        tuple: A tuple containing the refined beginning of the document and the 'todo' object used. 
        """
        instruction, context, confirmed = await self.planner.ask_review_template()
        if  not hasattr(self, 'rc') or not hasattr(self.rc, 'todo'):
            raise AttributeError("Expected 'rc' and 'rc.todo' to be initialized") 
        todo = self.rc.todo 
        refine_sets, cur_result = [], guidelines
        while  not confirmed:
            if  instruction == 'redo':
                refine_sets, cur_result = [], guidelines
                logger.info(f"Redo finished, revert to the original response.")
                instruction, context, confirmed = await self.planner.ask_review_template()
                continue
            refine_sets.append(cur_result)
            pre_result = '\n\n'.join(refine_sets[-3:])    # Retain up to 2 rounds of results
            cur_result = await Refine().run(
                                                        user_requirement = instruction,
                                                        original_query = chapter_name,
                                                        respones = pre_result,
                                                        contexts = context 
                                            )
            
            instruction, confirmed = await self.planner.ask_user_instruction()
        return cur_result,  todo
    
    @colored_decorator("\033[1;46m")
    async def doc_retrieve(self,title):
        """
        Retrieve relevant information from documents based on the given title.

        This method retrieves contexts from documents using an engine, which could be a retrieval or a RAG (Retrieval Augmented Generation) model.
        The retrieval mode is determined by the `rag_mode` attribute of the class instance. 
        The retrieved contexts are then optionally cleaned if the mode is set to 'retrieve_gen'.
        Parameters:
        title (str): The title or query used to retrieve relevant information from documents.
        Returns:
        contexts: A string containing the retrieved contexts, separated by section dividers.
        """
        if  not self.use_store:    
            return ''
        
        contexts = ''
        if self.store_mode == 'search':
            todo = self.actions[-1]
            prompt = f'Please help me write the content of chapter "{title}"' if self.store else title
            message = [Message(content= prompt, role="user", cause_by = UserRequirement)]
            contexts = await todo.run(self.rc.history  + message)     
            
        if  self.store_mode.startswith('retrieve'):
            # Retrieve contexts using the store's aretrieve method
            contexts = await self.store.aretrieve(title)    
            contexts = '\n\n'.join([x.text for x in contexts]) 
            if self.store_mode == 'retrieve_clean':             
               contexts =  await Clean().run(title = title, contexts = contexts)    
        return contexts
        
        
    async def add_nodes_doc(self):  
        """
        Add nodes to the document retriever engine based on the assistant's messages from memory.
        This method extracts text chunks from the working memory where the role is "assistant",
        creates Document objects with these chunks, and then adds these documents as nodes to the
        retriever engine.
        """
        if  not self.use_store or not self.store:
            return 
        text_chunks = [message.content for message in self.working_memory.get() if message.role == "assistant"] 
        doc_chunks = []
        for i, text in enumerate(set(text_chunks)):
            doc = Document(text=text, id_=f"doc_id_{i}")
            doc_chunks.append(doc)
        # Add the list of Document objects as nodes to the retriever engine
        self.store.retriever.add_nodes(doc_chunks)
        self.working_memory.clear()
        return 
    
    

    

                
