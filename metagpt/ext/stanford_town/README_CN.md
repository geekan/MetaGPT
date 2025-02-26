## Stanford Town Game

### 前置
为了方便GA（ [generative_agents](https://github.com/joonspk-research/generative_agents) ）的前端对接数据（避免改动它那块的代码），可在启动`run_st_game.py`加上`temp_storage_path`指向`generative_agents`对应的`temp_storage`路径。比如

`python3 run_st_game.py --temp_storage_path path/to/ga/temp_storage xxx`   

或将`const.py`下的

```
STORAGE_PATH = EXAMPLE_PATH.joinpath("storage")
TEMP_STORAGE_PATH = EXAMPLE_PATH.joinpath("temp_storage")
# 更新为
STORAGE_PATH = Path("{path/to/ga/storage}")
TEMP_STORAGE_PATH = Path("{path/to/ga/temp_storage}")
```
这样可用实现不改变GA代码情况下，实现仿真数据的对接。不然得修改GA的代码来适配MG的输出路径。  

如果你不想从0开始启动，拷贝`generative_agents/environment/frontend_server/storage/`下的其他仿真目录到`examples/stanford_town/storage`，并选择一个目录名作为`fork_sim_code`。  

### 后端服务启动
执行入口为：`python3 run_st_game.py "Host a open lunch party at 13:00 pm" "base_the_ville_isabella_maria_klaus" "test_sim" 10`  
或者  
`python3 run_st_game.py "Host a open lunch party at 13:00 pm" "base_the_ville_isabella_maria_klaus" "test_sim" 10 --temp_storage_path path/to/ga/temp_storage`

`idea`为用户给第一个Agent的用户心声，并通过这个心声进行传播，看最后多智能体是否达到举办、参加活动的目标。  

### 前端服务启动
进入`generative_agents`项目目录

进入`environment/frontend_server`，使用`python3 manage.py runserver`启动前端服务。  
访问`http://localhost:8000/simulator_home` 进入当前的仿真界面。  

## 致谢
复现工作参考了 [generative_agents](https://github.com/joonspk-research/generative_agents), 感谢相关作者们。

### 引用
```bib
@inproceedings{Park2023GenerativeAgents,  
author = {Park, Joon Sung and O'Brien, Joseph C. and Cai, Carrie J. and Morris, Meredith Ringel and Liang, Percy and Bernstein, Michael S.},  
title = {Generative Agents: Interactive Simulacra of Human Behavior},  
year = {2023},  
publisher = {Association for Computing Machinery},  
address = {New York, NY, USA},  
booktitle = {In the 36th Annual ACM Symposium on User Interface Software and Technology (UIST '23)},  
keywords = {Human-AI interaction, agents, generative AI, large language models},  
location = {San Francisco, CA, USA},  
series = {UIST '23}
}
```
