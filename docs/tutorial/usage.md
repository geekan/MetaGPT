## MetaGPT Usage

### Configuration

- Configure your `api_key` in any of `~/.metagpt/config2.yaml / config/config2.yaml`
- Priority order: `~/.metagpt/config2.yaml > config/config2.yaml`

```bash
# Copy the configuration file and make the necessary modifications.
cp config/config2.yaml ~/.metagpt/config2.yaml
```

### Initiating a startup

```shell
# Run the script
metagpt "Write a cli snake game"
# Do not hire an engineer to implement the project
metagpt "Write a cli snake game" --no-implement
# Hire an engineer and perform code reviews
metagpt "Write a cli snake game" --code_review
```

After running the script, you can find your new project in the `workspace/` directory.

### Preference of Platform or Tool

You can tell which platform or tool you want to use when stating your requirements.

```shell
metagpt "Write a cli snake game based on pygame"
```

### Usage

```
 Usage: metagpt [OPTIONS] [IDEA]                                                                                                                                                                                          
                                                                                                                                                                                                                          
 Start a new project.                                                                                                                                                                                                     
                                                                                                                                                                                                                          
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   idea      [IDEA]  Your innovative idea, such as 'Create a 2048 game.' [default: None]                                                                                                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --investment                                     FLOAT    Dollar amount to invest in the AI company. [default: 3.0]                                                                                                    │
│ --n-round                                        INTEGER  Number of rounds for the simulation. [default: 5]                                                                                                            │
│ --code-review                --no-code-review             Whether to use code review. [default: code-review]                                                                                                           │
│ --run-tests                  --no-run-tests               Whether to enable QA for adding & running tests. [default: no-run-tests]                                                                                     │
│ --implement                  --no-implement               Enable or disable code implementation. [default: implement]                                                                                                  │
│ --project-name                                   TEXT     Unique project name, such as 'game_2048'.                                                                                                                    │
│ --inc                        --no-inc                     Incremental mode. Use it to coop with existing repo. [default: no-inc]                                                                                       │
│ --project-path                                   TEXT     Specify the directory path of the old version project to fulfill the incremental requirements.                                                               │
│ --reqa-file                                      TEXT     Specify the source file name for rewriting the quality assurance code.                                                                                       │
│ --max-auto-summarize-code                        INTEGER  The maximum number of times the 'SummarizeCode' action is automatically invoked, with -1 indicating unlimited. This parameter is used for debugging the      │
│                                                           workflow.                                                                                                                                                    │
│                                                           [default: 0]                                                                                                                                                 │
│ --recover-path                                   TEXT     recover the project from existing serialized storage [default: None]                                                                                         │
│ --init-config                --no-init-config             Initialize the configuration file for MetaGPT. [default: no-init-config]                                                                                     │
│ --help                                                    Show this message and exit.                                                                                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```