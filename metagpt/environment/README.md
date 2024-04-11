Here is a environment description of MetaGPT env for different situation.  
For now, the code only define the environment and still some todos like migrate roles/actions to current version.

## Function
- Define `ExtEnv`(Base Class) which help users to integrate with external environment like games through apis or construct the game logics.
- Define `Environment`(Base Class) which is the env that MetaGPT directly used. And it includes roles and so on.
- Define the `EnvAPIRegistry` to mark the read/write apis that `ExtEnv` provide observe/step ability. And then, users can call the particular one to get observation from env or feedback to env.

## Usage

init environment
```
android_env = env.create(EnvType.ANDROID)

assistant = Role(name="Bob", profile="android assistant")
team = Team(investment=10.0, env=android_env, roles=[assistant])
```

observe & step inside role's actions
```
from metagpt.environment.api.env_api import EnvAPIAbstract

# get screenshot from ExtEnv
screenshot_path: Path = await env.observe(
            EnvAPIAbstract(
                api_name="get_screenshot", kwargs={"ss_name": f"{round_count}_before", "local_save_dir": task_dir}
            )
        )

# do a `tap` action on the screen
res = env.step(EnvAPIAbstract("system_tap", kwargs={"x": x, "y": y}))
```

## TODO
- add android app operation assistant under `examples/android_assistant`
- migrate roles/actions of werewolf game from old version into current version
- migrate roles/actions of minecraft game from old version into current version
- migrate roles/actions of stanford_town game from old version into current version
