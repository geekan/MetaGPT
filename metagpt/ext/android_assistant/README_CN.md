# MetaGPT 安卓助理

MetaGPT安卓助理是一款依托于先进的MetaGPT框架构建的多模态大语言模型驱动的智能辅助工具。
它具备自我学习的能力，能够通过学习掌握用户的日常使用方式，同时能够根据用户的指令自动完成各类应用程序的操作任务，实现了用户双手的全面解放。
接下来，我们将介绍MetaGPT安卓助理的功能以及如何使用它。

## 功能

MetaGPT 安卓助理的执行主要包含两个阶段，分别为自我学习与自动执行。下面，我们将从这两个阶段介绍MetaGPT 安卓助理的具体功能。

### 自我学习阶段

通过学习人类演示或基于人类指令对app进行探索，MetaGPT安卓助理可以对app的功能进行学习，生成相应的操作文档，为后续的“自动执行”阶段使用。对于任何给定的任务目标，进行约20轮的探索可以显著提高性能。

通过设定`stage`为`learn`可要求安卓助理进入自我学习阶段。通过设定`mode`为`auto`，可要求安卓助理通过自动探索学习，通过设定`mode`为`manual`，可要求安卓助理通过人类手动演示学习。在使用章节，我们对脚本的参数进行了详细的说明。
您可以尝试对“Messenger”应用程序进行自动探索和手动演示模式的实验，具体命令如下：

```bash
cd examples/android_assistant
python run_assistant.py "Send 'When will we release this feature? to +86 8888888'" --stage "learn" --mode "auto or manual" --app-name "Messenger"
```

#### 基于人类演示的学习
在要求安卓助理在自我学习阶段执行自我探索时，您可以解放您的双手，但在要求他根据您的指令进行学习时，你需要根据终端中的指令进行输入，以便安卓助理能够准确地学习您的操作方式。
一个可能的例子如下：

```bash
cd examples/android_assistant
python run_assistant.py "Send 'When will we release this feature? to +86 8888888'" --stage "learn" --mode "manual" --app-name "Messenger"
```

在运行这一指令后，你将首先看到一个在各个可交互的位置进行了标记的安卓屏幕的截图，如下图：

<img src="./resources/manual_example.png" width = 30%>

在记住你要操作的位置之后，终端中将会输出与下面类似的要求，回复它，进而指挥安卓助理学习你的演示行为：

```bash
| INFO     | examples.android_assistant.actions.manual_record:run:96 - Which element do you want to tap? Choose a numeric tag from 1 to 11:
user_input: 8
| INFO     | examples.android_assistant.actions.manual_record:run:81 - Choose one of the following actions you want to perform on the current screen:
tap, text, long_press, swipe, stop
user_input: tap
```
### 自动执行阶段
在安卓助理完成了自我学习阶段之后，您可以通过文本描述的方式，指挥安卓助理在手机中完成任务。通过为其配置自我学习阶段的操作文档，安卓助理具备了更丰富的前置知识，执行能力进一步得到提升。
你可以通过以下指令，指挥安卓助理在“Messenger”应用中发送信息：
```bash
python run_assistant.py "Send 'When will we release this feature? to +86 8888888'" --stage "act" --mode "auto or manual" --app-name "Messenger"
```
其中，`mode`选择`auto`，安卓助理将使用自我探索中积累的操作文档；`mode`选择`manual`，安卓助理将使用人类演示学习中积累的操作文档。

## 安装
为了使用安卓助理，你首先需要满足以下条件：
1. 完成MetaGPT环境的安装
2. 在你的PC上安装[Android Debug Bridge(ADB)](https://developer.android.com/tools/adb?hl=zh-cn)，ADB可以使你的PC与安卓设备进行交互。
3. 安装Android Studio，在其中安装Android模拟器，以为安卓助手提供学习与执行的环境。关于如何安装Android模拟器，可以参考[快速安装Android Studio & Emulator](https://dev.weixin.qq.com/docs/framework/dev/framework/env/android-simulator.html)。
4. (Optional) 将你的安卓设备连接到PC的USB端口上，这同样可以为安卓助手提供学习与执行的环境。

注意 ⚠️：在使用Android模拟器进行操作时，我们使用的模拟器型号为Medium Phone，建议第一次尝试此类应用的用户使用这一型号完成操作。

在完成这一系列操作之后，你可以输入以下命令检查ADB是否安装成功，以及安卓设备是否连接
```bash
adb devices
```
## 使用
MetaGPT 安卓助理在MetaGPT框架中被设计为一个`Role`与多个`Action`的集合，你可以通过运行`run_assistant.py`脚本来运行它。这一脚本具体的参数说明如下：
```text
用法：run_assistant.py [选项] 任务描述

  运行一个安卓助手

参数：
  TASK_DESC  你希望安卓助手学习或执行的任务描述
              [必需]

选项：
  --n-round 整数               执行应用程序操作任务的最大轮数。
                                  [默认值：20]
  --stage 文本                   阶段：learn/act  [默认值：learn]
  --mode 文本                    模式：auto/manual，当状态=learn时 [默认值：auto]
  --app-name 文本                你想要运行的应用程序名称  [默认值：
                                  演示]
  --investment 浮点数             投资于人工智能公司的美元金额。
                                  [默认值：5.0]
  --refine-doc / --no-refine-doc  如果为真，则根据最新的观察结果优化现有操作文档。
                                  [默认值：--no-refine-doc]
  --min-dist 整数              在标记过程中防止元素重叠的最小元素间距。
                                  [默认值：30]
  --android-screenshot-dir 文本  在安卓设备上存储截图的路径。确保其存在。
                                  [默认值：/sdcard/Pictures/Screenshots]
  --android-xml-dir 文本         存储用于确定UI元素位置的XML文件的路径。
                                  确保其存在。[默认值：/sdcard]
  --device-id 文本               安卓device_id  [默认值：
                                  模拟器-5554]
  --help                          显示此信息并退出。
```

## 致谢
MetaGPT 安卓助理参考了 [AppAgent](https://github.com/mnotgod96/AppAgent) 项目的部分思路与代码，感谢 Appagent 项目的开发者们。

### 引用

```bib
@misc{yang2023appagent,
      title={AppAgent: Multimodal Agents as Smartphone Users}, 
      author={Chi Zhang and Zhao Yang and Jiaxuan Liu and Yucheng Han and Xin Chen and Zebiao Huang and Bin Fu and Gang Yu},
      year={2023},
      eprint={2312.13771},
      archivePrefix={arXiv},
      primaryClass={cs.CV}
}
```