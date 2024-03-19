## Docker安装

### 使用MetaGPT镜像

```bash
# 步骤1: 下载metagpt官方镜像并准备好config2.yaml
docker pull metagpt/metagpt:latest
mkdir -p /opt/metagpt/{config,workspace}
docker run --rm metagpt/metagpt:latest cat /app/metagpt/config/config2.yaml > /opt/metagpt/config/config2.yaml
vim /opt/metagpt/config/config2.yaml # 修改配置文件

# 步骤2: 使用容器运行metagpt演示
docker run --rm \
    --privileged \
    -v /opt/metagpt/config/config2.yaml:/app/metagpt/config/config2.yaml \
    -v /opt/metagpt/workspace:/app/metagpt/workspace \
    metagpt/metagpt:latest \
    metagpt "Write a cli snake game"

# 您也可以启动一个容器并在其中执行命令
docker run --name metagpt -d \
    --privileged \
    -v /opt/metagpt/config/config2.yaml:/app/metagpt/config/config2.yaml \
    -v /opt/metagpt/workspace:/app/metagpt/workspace \
    metagpt/metagpt:latest

docker exec -it metagpt /bin/bash
$ metagpt "Write a cli snake game"
```

`docker run ...`做了以下事情:

- 以特权模式运行，有权限运行浏览器
- 将主机文件 `/opt/metagpt/config/config2.yaml` 映射到容器文件 `/app/metagpt/config/config2.yaml`
- 将主机目录 `/opt/metagpt/workspace` 映射到容器目录 `/app/metagpt/workspace`
- 执行示例命令 `metagpt "Write a cli snake game"`

### 自己构建镜像

```bash
# 您也可以自己构建metagpt镜像
git clone https://github.com/geekan/MetaGPT.git
cd MetaGPT && docker build -t metagpt:custom .
```
