from __future__ import annotations
from metagpt.actions import Action
from metagpt.schema import Message
BEGGING_PROMPT = """
# user requirements
   {user_requirement}
# the current chapter title
   {chapter_name}
# the subheadings
   {subheadings}
# Selective reference
   {contexts}
# Task:
   Based on the user's specified writing topic and considering the current chapter title, its subheadings, and selective reference, 
   assist in crafting an introductory preamble for this chapter. 
   The preamble should serve as a guiding statement that sets the stage for the content to follow, highlighting the central theme and providing a roadmap for the subheadings.

# Constraint:
   1. Integrate insights from the subheadings to enrich the content.
   2. Keep the expansion to approximately 10 sentences for brevity.
   3. Ensure the response is clear and concise, avoiding unnecessary elaboration.
   4. The response should be provided in {language} to align with the user's requirements.
"""

class WriteGuide(Action):
    async def run(  self,
                    user_requirement: str,
                    chapter_name : str,
                    subheadings  : str,
                    contexts : str,
                    language : str = 'chinese'
                    ) -> str:      
        structual_prompt = BEGGING_PROMPT.format(
            user_requirement=user_requirement,
            chapter_name = chapter_name,
            subheadings =  subheadings,
            contexts = contexts,
            language = language
            )
        
        context = self.llm.format_msg([Message(content=structual_prompt, role="user")])
        rsp = await self.llm.aask(context)
        return rsp

REFINE = """
# user's guidance:
   {user_requirement}
   
# original answer:
   {respones}   
   
# Additional Context: 
   {contexts}    
   
# task:
   Enhance the clarity and effectiveness of the original answer to the query “{original_query}” by incorporating the user's guidance and the additional context provided.

# Constraints:
1. If the additional context proves irrelevant or lacks substance, default to providing the initial response without modification.
2. Ensure that the refined answer is coherently integrated and maintains a high level of logical flow and readability.

# Instructions:
- The response should be provided in {language} to align with the user's requirements.
- Carefully review the user's guidance to understand the desired improvements.
- Assess the additional context for its relevance and potential to enhance the original answer.
- Modify the original answer by adding, removing, or rephrasing content as necessary to align with the user's guidance and the new context.
- Proofread the refined answer to ensure it is clear, concise, and effectively addresses the original query.
- Maintain the integrity of the original response while incorporating the enhancements.
"""

class Refine(Action):
    async def run(  self,
                    original_query: str,
                    respones : str,
                    contexts  : str,
                    user_requirement : str = '',
                    language : str = 'chinese',
                    **kwargs) -> str:    
        original_query = f"{original_query}"  
        structual_prompt = REFINE.format(
            original_query = original_query,
            respones = respones,
            contexts = contexts,
            user_requirement = user_requirement,
            language = language
            )
        context = self.llm.format_msg([Message(content=structual_prompt, role="user")])
        rsp = await self.llm.aask(context, **kwargs)
        return rsp


SUBSECTION_PROMPT = """
# user requirements:
   To generate a comprehensive paragraph that elaborates on the given subsection heading within the provided context.
   
# the subsection heading: Begin by identifying the specific subsection heading provided.
   {subsection}
   
# Contextual Preamble: Consider the introductory context that sets the stage for the subsection. 
   {contexts}
   
# Writing Guidelines:
   Step 1: Reflect on the subsection heading and how it relates to the preamble.
   Step 2: Develop a coherent paragraph that builds upon the preamble and directly addresses the subsection heading.
   Step 3: Ensure the paragraph is enriched with relevant details, examples, or explanations that enhance understanding.
   Step 4: Review the paragraph for clarity, coherence, and adherence to the subsection's focus.

# Instructions:
   1. Align with Subsection Heading:
      Ensure that your content directly corresponds to the topic outlined by the subsection heading. This alignment is crucial for maintaining coherence and relevance throughout the document.
   2. Follow Specified Headings:
      Strictly adhere to the headings provided. Each section should be crafted to specifically address and expand upon the ideas presented in these headings.
   3. Focus on Content Depth:
      Concentrate on developing the substance of your writing around the core theme indicated by the subsection heading. Where applicable, enrich your discussion with relevant references to support your arguments and enhance credibility.  
"""
       
class WriteSubsection(Action):
    async def run( self, subsection  : str,  contexts : str,  **kwargs) -> str:     
        structual_prompt = SUBSECTION_PROMPT.format( subsection = subsection,
                                                     contexts = contexts
                                                    )
        context = self.llm.format_msg([Message(content=structual_prompt, role="user")])
        rsp = await self.llm.aask(context, **kwargs)
        return rsp
    

CLC_PROMPT = """ 
# Title: 
   {title}
# Provided contexts:
   ```
   {contexts}
   ```  
# task:
  Extract key information pertinent to the title from the provided context to ensure that the data extracted accurately reflects the subject matter. 
  If the context contains no relevant information, return an empty result. Focus on filtering out any irrelevant or non-useful data to maintain the accuracy and relevance of the extracted content.

# Constraints: 
  1. Keep the expansion to approximately 5 sentences for brevity.
  2. The response should be provided in {language}.
"""
class Clean(Action):
    async def run(self,title: str,contexts: str, language:str = 'chinese') -> str:    
      structual_prompt = CLC_PROMPT.format(
            title = title,
            contexts = contexts,
            language = language
            )
      context = self.llm.format_msg([Message(content=structual_prompt, role="user")])
      rsp = await self.llm.aask(context)
      return rsp  