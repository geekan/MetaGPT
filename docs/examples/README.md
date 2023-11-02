## Examples
We introduce some example agents created recently and show how to created these agents under the framework.

- Researcher
  - With the given research topic, the agent will derive the keywords from the topic and then search the related documents using search engine api.
  - The search result will be ranked and filtered to get high quality candidates.
  - Summary the final content using the candidate documents as context. 
- Invoice OCR and QA  
  - With the given one or multi invoices, the agent can recognize the text from the image or pdf.
  - Organize the text with particular structure, generally, it will be saved in a csv.
  - It can answer your question like `what's the total reimbursement of Alice?`  
- Werewolf Game
