## MetaGPT 使用

### 配置

- 在 `config/key.yaml / config/config.yaml / env` 中配置您的 `OPENAI_API_KEY`
- 优先级顺序：`config/key.yaml > config/config.yaml > env`

```bash
# 复制配置文件并进行必要的修改
cp config/config.yaml config/key.yaml
```

| 变量名                              | config/key.yaml                           | env                                             |
| ----------------------------------- | ----------------------------------------- | ----------------------------------------------- |
| OPENAI_API_KEY # 用您自己的密钥替换 | OPENAI_API_KEY: "sk-..."                  | export OPENAI_API_KEY="sk-..."                  |
| OPENAI_API_BASE # 可选              | OPENAI_API_BASE: "https://<YOUR_SITE>/v1" | export OPENAI_API_BASE="https://<YOUR_SITE>/v1" |

### 示例：启动一个创业公司

```shell
python startup.py "写一个命令行贪吃蛇"
# 开启code review模式会花费更多的金钱, 但是会提升代码质量和成功率
python startup.py "写一个命令行贪吃蛇" --code_review True
```

运行脚本后，您可以在 `workspace/` 目录中找到您的新项目。

### 平台或工具的倾向性
可以在阐述需求时说明想要使用的平台或工具。
例如：
```shell
python startup.py "写一个基于pygame的命令行贪吃蛇"
```

### 使用

```
名称
    startup.py - 我们是一家AI软件创业公司。通过投资我们，您将赋能一个充满无限可能的未来。

概要
    startup.py IDEA <flags>

描述
    我们是一家AI软件创业公司。通过投资我们，您将赋能一个充满无限可能的未来。

位置参数
    IDEA
        类型: str
        您的创新想法，例如"写一个命令行贪吃蛇。"

标志
    --investment=INVESTMENT
        类型: float
        默认值: 3.0
        作为投资者，您有机会向这家AI公司投入一定的美元金额。
    --n_round=N_ROUND
        类型: int
        默认值: 5

备注
    您也可以用`标志`的语法，来处理`位置参数`
```
