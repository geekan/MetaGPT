# MetaGPT Android Assistant

The MetaGPT Android Assistant is an intelligent assistance tool driven by a multi-modal large language model based on the advanced MetaGPT framework.  It has the ability to self-learn, mastering users' daily usage patterns through learning, and can automatically complete various application operations according to user instructions, achieving comprehensive liberation of users' hands.
Next, we will introduce the functions of the MetaGPT Android Assistant and how to use it.

## Features

The operation of the MetaGPT Android Assistant mainly includes two stages: learning and automatic execution. Below, we introduce the specific features of the MetaGPT Android Assistant from these two stages.

### Learning Stage

By learning from human demonstrations or exploring apps based on human instructions, the MetaGPT Android Assistant can learn the functionality of apps, generate corresponding operation documents for use in the subsequent "automatic execution" stage. Approximately 20 rounds of exploration for any given task objective can significantly improve performance.

By setting the `stage` to `learn`, you can ask the Android Assistant to enter the learning stage. By setting the `mode` to `auto`, you can instruct the Android Assistant to learn through automatic exploration; by setting the mode to manual, you can instruct the Android Assistant to learn through human manual demonstration. In the usage section, we provide detailed explanations of the script parameters. You can try experimenting with automatic exploration and manual demonstration modes on the "Messenger" app with the following commands:

```bash
cd examples/android_assistant
python run_assistant.py "Send 'When will we release this feature?' to +86 8888888" --stage "learn" --mode "auto or manual" --app-name "Messenger"
```

#### Learning Based on Human Demonstration
When asking the Android Assistant to perform self-exploration during the learning stage, you can free your hands. However, when instructing it to learn according to your commands, you need to follow the instructions in the terminal for the Android Assistant to accurately learn your operation methods.
A possible example is as follows:

```bash
cd examples/android_assistant
python run_assistant.py "Send 'When will we release this feature?' to +86 8888888" --stage "learn" --mode "manual" --app-name "Messenger"
```

After running this command, you will first see a screenshot of an Android screen that has been marked at various interactive locations, as shown in the figure below:

<img src="./resources/manual_example.png" width = 30%>

After remembering the location where you want to operate, a request similar to the one below will be output in the terminal. Reply to it and thereby direct the Android assistant to learn your demonstration action:

```bash
| INFO     | examples.android_assistant.actions.manual_record:run:96 - Which element do you want to tap? Choose a numeric tag from 1 to 11:
user_input: 8
| INFO     | examples.android_assistant.actions.manual_record:run:81 - Choose one of the following actions you want to perform on the current screen:
tap, text, long_press, swipe, stop
user_input: tap
```

### Automatic Execution Stage
After the Android Assistant completes the learning stage, you can command it to complete tasks on the phone through text descriptions. By configuring the operation documents from the self-learning stage, the Android Assistant has richer prior knowledge, and its execution capabilities are further enhanced.
You can instruct the Android Assistant to send messages in the "Messenger" app with the following command:
```bash
python run_assistant.py "Send 'When will we release this feature?' to +86 8888888" --stage "act" --mode "auto or manual" --app-name "Messenger"
```
Specifically, by selecting `auto` for `mode`, the Android assistant will employ the operational records compiled through self-exploration. Alternatively, if `manual` is chosen as the `mode`, the Android assistant will leverage the operation manuals accrued from learning via human demonstration.

## Installation
To use the Android Assistant, you first need to meet the following conditions:
1. Complete the installation of the MetaGPT environment.
2. Install [Android Debug Bridge (ADB)](https://developer.android.com/tools/adb?hl=zh-cn) on your PC, which enables interaction between your PC and Android devices.
3. Install Android Studio and within it, install the Android emulator to provide an environment for the Android Assistant to learn and execute. For information on how to install the Android emulator, refer to [Quick Installation of Android Studio & Emulator](https://docs.expo.dev/workflow/android-studio-emulator/).
4. (Optional) Connect your Android device to the USB port of your PC, which can also provide an environment for the Android Assistant to learn and execute.

Note ⚠️: When operating with the Android emulator, the emulator model we use is Medium Phone, which is recommended for first-time users to complete the operation.

After completing these operations, you can enter the following command to check if ADB is installed successfully and if the Android device is connected:
```bash
adb devices
```

## Usage
The MetaGPT Android Assistant is designed within the MetaGPT framework as a collection of Roles and multiple Actions. You can run it by executing the `run_assistant.py` script. The specific parameter description of this script is as follows:
```text
Usage: run_assistant.py [OPTIONS] TASK_DESC

  Run a Android Assistant

Arguments:
  TASK_DESC  the task description you want the android assistant to learn or
             act  [required]

Options:
  --n-round INTEGER               The max round to do an app operation task.
                                  [default: 20]
  --stage TEXT                    stage: learn / act  [default: learn]
  --mode TEXT                     mode: auto / manual , when state=learn
                                  [default: auto]
  --app-name TEXT                 the name of app you want to run  [default:
                                  demo]
  --investment FLOAT              Dollar amount to invest in the AI company.
                                  [default: 5.0]
  --refine-doc / --no-refine-doc  Refine existing operation docs based on the
                                  latest observation if True.  [default: no-
                                  refine-doc]
  --min-dist INTEGER              The minimum distance between elements to
                                  prevent overlapping during the labeling
                                  process.  [default: 30]
  --android-screenshot-dir TEXT   The path to store screenshots on android
                                  device. Make sure it exists.  [default:
                                  /sdcard/Pictures/Screenshots]
  --android-xml-dir TEXT          The path to store xml files for determining
                                  UI elements localtion. Make sure it exists.
                                  [default: /sdcard]
  --device-id TEXT                The Android device_id  [default:
                                  emulator-5554]
  --help                          Show this message and exit.
```

## Acknowledgements
The MetaGPT Android Assistant has referenced some ideas and code from the [AppAgent](https://github.com/mnotgod96/AppAgent) project. We thank the developers of the Appagent project.

### Citation

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