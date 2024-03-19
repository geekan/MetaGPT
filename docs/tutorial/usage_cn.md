## MetaGPT 使用

### 配置

- 在 `~/.metagpt/config2.yaml / config/config2.yaml` 中配置您的 `api_key`
- 优先级顺序：`~/.metagpt/config2.yaml > config/config2.yaml`

```bash
# 复制配置文件并进行必要的修改
cp config/config2.yaml ~/.metagpt/config2.yaml
```

### 示例：启动一个创业公司

```shell
metagpt "写一个命令行贪吃蛇"
# 开启code review模式会花费更多的金钱, 但是会提升代码质量和成功率
metagpt "写一个命令行贪吃蛇" --code_review
```

运行脚本后，您可以在 `workspace/` 目录中找到您的新项目。

### 平台或工具的倾向性
可以在阐述需求时说明想要使用的平台或工具。
例如：
```shell
metagpt "写一个基于pygame的命令行贪吃蛇"
```

### 使用

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
