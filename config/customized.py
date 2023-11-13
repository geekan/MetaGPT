# Configurations for customizing LLM
# Ability to select a specific LLM as a base for an Action or Role
# Need to provide an interface similar to OPENAI
"""
@Time    : 2023/11/13 15:08
@Author  : Yangqianli
@File    : customized.py
"""
ALL_ROLES = [
    "Architect","CustomerService","Engineer","InvoiceOCRAssistant","ProductManager","ProjectManager","PromptString",
    "QaEngineer","Researcher","Sales","Searcher","SkAgent","TutorialAssistant"
]

ALL_ACTIONS = [
    "ActionOutput","BossRequirement","AnalyzeDepLibs","AzureTTS","CloneFunction","DebugError","WriteDesign",
    "DesignReview","DesignFilenames","DetailMining","ExecuteTask","InvoiceOCR","PrepareInterview","WriteTasks",
    "AssignTasks","CollectLinks","WebBrowseAndSummarize","ConductResearch","RunCode","SearchAndSummarize",
    "WriteCode","WriteCodeReview","WriteDocstring","WritePRD",
    "WritePRDReview","WriteTest","WriteDirectory","WriteContent"
]

# You can customize the LLM for each Role/Action here 
# if it is None or not set, it will use the default settings in config.yaml

ROLE_LLMS_MAPPING = {
    "ProductManager":{
        'llm':{
            "api":"http://xxx.xx.xx.xx:xxxxx/v1",
            "model_name":"llama2-13b-chat-hf"
        }
    },

    "Architect": None,

    "ProjectManager":{
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
    "Engineer":{
        'llm':{
            "api":"http://xxx.xx.xx.xx:xxxxx/v1",
            "model_name":"llama2-13b-chat-hf"
        }
    },
    "QaEngineer":{
        'llm':{
            "api":"http://xxx.xx.xx.xx:xxxxx/v1",
            "model_name":"llama2-13b-chat-hf"
        }
    }
}

ACTION_LLMS_MAPPING = {

    "BossRequirement":None,

    "WriteCode":{
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
    "WritePRD":{
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
    "WriteDesign":{
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
    "WriteTasks":{
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
    "WriteCodeReview":{
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
    "WriteTest":{
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
    "RunCode": {
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
    "DebugError": {
        'llm':{
            "api":"https://api.openai.com/v1",
            "model_name":"gpt-3.5-turbo-16k-0613"
        }
    },
}

