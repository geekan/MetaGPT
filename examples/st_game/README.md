## Stanford Town Game

### Pre-Description
The path configured in `examples/st_game/utils/const.py` is the storage path of the current project. In order to facilitate GA( [generative_agents](https://github.com/joonspk-research/generative_agents) )'s frontend docking data (to avoid changing its code), you can set the value `temp_storage_path` to `temp_storage` of `generative_agents` when start `run_st_game.py`. like 

`python3 run_st_game.py --temp_storage_path path/to/ga/temp_storage xxx`  

Or change the path under `const.py` like beflow  

```
STORAGE_PATH = ROOT_PATH.joinpath("storage")
TEMP_STORAGE_PATH = ROOT_PATH.joinpath("temp_storage")
# updated
STORAGE_PATH = Path("{path/to/ga/storage}")
TEMP_STORAGE_PATH = Path("{path/to/ga/temp_storage}")
```

This can be used to achieve docking of simulation data without changing the GA code. Otherwise, the GA code must be modified to adapt to the MG output path.  

If you don't want to start from 0, copy other simulation directories under `generative_agents/environment/frontend_server/storage/` to `examples/st_game/storage`, and select a directory named `fork_sim_code`.  

### Backend service startup
The execution entry is `python3 run_st_game.py "Host a open lunch party at 13:00 pm" "base_the_ville_isabella_maria_klaus" "test_sim" 10`  
or   
`python3 run_st_game.py "Host a open lunch party at 13:00 pm" "base_the_ville_isabella_maria_klaus" "test_sim" 10 --temp_storage_path path/to/ga/temp_storage`  

`idea` is the user's voice to the first Agent, and it is disseminated through this voice to see whether the final multi-agents achieve the goal of hosting or participating in the event.  

### Frontend service startup
Enter project folder `generative_agents`  

Enter `environment/frontend_server` and use `python3 manage.py runserver` to start the front-end service.  
Visit `http://localhost:8000/simulator_home` to enter the current simulation interface.  

## Appreciation
The reproduction work has referred the `https://github.com/joonspk-research/generative_agents`, let's make a general statement here.  
