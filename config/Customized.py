# 均为类名，而非init中的name
# 也可以考虑直接用类作为key
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


#CODE_API = "https://api.openai.com/v1"
#CODE_MODEL = "gpt-3.5-turbo-0613"
CODE_API = "https://api.openai-forward.com/v1"
CODE_MODEL="gpt-3.5-turbo-16k-0613"
# NOCODE_API = "https://api.openai-forward.com/v1"
# NOCODE_MODEL="gpt-3.5-turbo-16k-0613"
NOCODE_API = "http://106.75.10.65:17865/v1"
NOCODE_MODEL="llama2-13b-chat-hf"

ROLE_LLMS_MAPPING = {
    "ProductManager":{
        'llm':{
            "api":NOCODE_API,
            "model_name":NOCODE_MODEL
        }
    },

    "Architect": None,

    "ProjectManager":{
        'llm':{
            "api":NOCODE_API,
            "model_name":NOCODE_MODEL
        }
    },
    "Engineer":{
        'llm': {
            "api":NOCODE_API,
            "model_name":NOCODE_MODEL
        }
    },
    "QaEngineer":{
        'llm': {
            "api": NOCODE_API,
            "model_name": NOCODE_MODEL
        }
    }
}

ACTION_LLMS_MAPPING = {

    "BossRequirement":None,

    "WriteCode":{
        'llm': {
            "api":CODE_API,
            "model_name":CODE_MODEL
        }
    },
    "WritePRD":{
        'llm': {
            "api":NOCODE_API,
            "model_name":NOCODE_MODEL
        }
    },
    "WriteDesign":{
        'llm': {
            "api":NOCODE_API,
            "model_name":NOCODE_MODEL
        }
    },
    "WriteTasks":{
        'llm': {
            "api":NOCODE_API,
            "model_name":NOCODE_MODEL
        }
    },
    "WriteCodeReview":{
        'llm': {
            "api":CODE_API,
            "model_name":CODE_MODEL
        }
    },
    "WriteTest":{
        'llm': {
            "api":CODE_API,
            "model_name":CODE_MODEL
        }
    },
    "RunCode": {
        'llm': {
            "api": CODE_API,
            "model_name": CODE_MODEL
        }
    },
    "DebugError": {
        'llm': {
            "api": CODE_API,
            "model_name": CODE_MODEL
        }
    },
}

