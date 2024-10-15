import fire
from pathlib import Path
from metagpt.const import DATA_PATH
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import FAISSRetrieverConfig, BM25RetrieverConfig, BGERerankConfig,FAISSIndexConfig
from metagpt.ext.ai_writer.writer import DocumentWriter
from metagpt.ext.ai_writer.utils import  WriteOutFile

def build_engine(ref_dir: Path, persist_dir: Path, model_name: str = "bge-large-zh") -> SimpleEngine:
    retriever_configs = [FAISSRetrieverConfig(similarity_top_k=10), BM25RetrieverConfig(similarity_top_k=20)]
    ranker_configs = [BGERerankConfig(model=model_name, top_n=10)]

    if persist_dir.exists():
        engine = SimpleEngine.from_index(index_config=FAISSIndexConfig(persist_path=persist_dir),
                                       retriever_configs=retriever_configs,
                                       ranker_configs=ranker_configs)
    else:
        engine = SimpleEngine.from_docs(input_dir=ref_dir,
                                        retriever_configs=retriever_configs,
                                        ranker_configs=ranker_configs)
        engine.retriever.persist(persist_dir=persist_dir)
    return engine



REQUIREMENT = "写一个完整、连贯的《{topic}》文档, 确保文字精确、逻辑清晰，并保持专业和客观的写作风格。"
topic = "产业数字化对中国出口隐含碳的影响"

async def main(auto_run: bool = False, use_store:bool = True):
    ref_dir     = DATA_PATH / f"ai_writer/ref/{topic}"
    persist_dir = DATA_PATH / f"ai_writer/persist/{topic}"
    output_path = DATA_PATH / f"ai_writer/outputs"
    model ='model/bge-large-zh-v1.5'
    
    if use_store:
       store = build_engine(ref_dir,persist_dir,model)
       dw = DocumentWriter(auto_run=auto_run,store = store) 
    else:
       dw = DocumentWriter(auto_run=auto_run,use_store = False)      
    
    requirement = REQUIREMENT.format(topic = topic)
    await dw.run(requirement)
    
    # write out word
    WriteOutFile.write_word_file(topic = topic, 
                tasks= dw.planner.titlehierarchy.traverse_and_output(),
                output_path = output_path)
    
if __name__ == "__main__":
    fire.Fire(main)
