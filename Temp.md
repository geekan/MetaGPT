## MG-MC记录文档

### 0926： 环境信息获取和更新 on_event()实际内容

1. Nodejs + Mineflayer配置

  A.自行安装[Node.js (nodejs.org)](https://nodejs.org/en)

  B.Mineflayer配置

  ```bash
  cd metagpt/mineflayer_env/mineflayer
  npm install -g npx
  npm install
  cd mineflayer-collectblock
  npm install
  npx tsc
  cd ..
  npm install
  ```



2.配置完游戏后，在 minecraft_run.py 下修改

```python
    mc_player.set_port(2465) # Modify this to your LAN port
```

python minecraft_run.py

<img src="docs/resources/workspace/minecraft_tests/on_event.jpeg" style="zoom:67%;" />

