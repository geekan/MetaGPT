# The Android Assisant
The Android assistant can learn from your daily operations or automatically learn, and perform App operations according to your instructions, thereby realizing any of your needs on the phone and freeing up your hands.  

## Install

### Device Simulator
1. Firstly, install ADB on the PC, which enables your PC to interact with Android devices
2. Connect the Android device to the computer's USB port
3. If you do not have an Android device, you can download Android Studio and use its Android emulator to carry out the subsequent operations. The steps to install the Android emulator can be found here:[快速安装Android Studio & Simulator](https://dev.weixin.qq.com/docs/framework/dev/framework/env/android-simulator.html)）

### Install Requirments
You can run the following command line:
```bash
pip install -r requirements.txt
```
## Experiential Learning
By designating the app to explore and the method of learning (automatic or manual demonstration), you can facilitate Android Assistant to master the functions of various apps, thereby generating respective documentation for later use during the phase termed as "Automation of routine tasks". For any given task objective, conducting approximately 20 cycles of exploration can considerably enhance the performance. You can experiment with both the automatic learning and manual demonstration modes for the "contacts" app by implementing the ensuing commands:

```bash
python run_assistant.py "your task description" --stage "learn" --mode "auto or manual" --app-name "Contacts"
```
## Free Your Hands
Once the Android Assistant has completed ample exploration, you are all set to automate your tasks! By utilizing either text description or voice input, you can instruct the Android Assistant to perform the desired tasks across various applications. For the specific command processes, please see the following recommendations:
### By Text
```bash
python run_assistant.py "your task description" --stage "act" --mode "auto or manual" --app-name "app names"
```
### By Voice
coming soon

## Run It
You can run Android Assisant by running the following command line:
```bash
python run_assistant.py "your task description" --stage "your choice(learn or act)" --mode "your choice(auto or manual)" --app-name "app name"
```
And the specific parameters are as follows:
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
