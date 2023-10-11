import re
import argparse
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math

def extract_logs(filename, start_time=None, end_time=None):
    with open(filename, 'r') as f:
        lines = f.readlines()

    if start_time is None or end_time is None:
        # 如果没有提供时间参数，则返回所有日志
        return lines

    # 截取开始时间和停止时间之间的日志块
    logs_block = []
    capture = False
    for line in lines:
        if start_time in line:
            capture = True
        if capture:
            logs_block.append(line)
        if end_time in line:
            capture = False
            break

    return logs_block

def extract_time_from_last_round_zero(log_filename):
    with open(log_filename, 'r') as f:
        lines = f.readlines()

    # 倒序遍历文件的每一行
    for line in reversed(lines):
        if "check msg round :0" in line:
            # 正则表达式匹配年月日 小时:分钟的格式
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
            if match:
                return match.group(1)
    return None

def analyze_log_block(logs_block):
    rounds: list[int] = []
    items_collected :list[int] = []
    total_items = 0
    positions:list[(int,int,int)] = []

    check_for_info = False  # 用于检查是否应在下几行中查找 Inventory 的标志
    line_after_message = 0  # 从 "Critic Agent human message" 开始计数的行数


    for line in logs_block:
        if "check msg round :" in line:
            n = int(re.search(r'check msg round :(\d+)', line).group(1))
            if n not in rounds:
                rounds.append(n)
                items_collected.append(total_items)  # add previous total before updating
        if "Critic Agent human message" in line:
            check_for_info = True
            line_after_message = 0
            continue

        if check_for_info:
            line_after_message += 1

            if line_after_message <= 20:
                if "Position: x=" in line:
                    match = re.search(r'Position: x=([\d.-]+), y=([\d.-]+), z=([\d.-]+)', line)
                    if match:
                        x, y, z = float(match.group(1)), float(match.group(2)), float(match.group(3))
                        positions.append((x, y, z))

                if "Inventory (" in line:
                    if ": Empty" in line:
                        check_for_info = False
                        continue
                    items = re.search(r'Inventory \(\d+/36\): ({.*?})', line).group(1)
                    items_dict = eval(items)
                    total_items = sum(items_dict.values())
                    check_for_info = False

    return rounds, items_collected,positions

def save_item_results_png(rounds, items_collected, start_time, path_prefix):
    # item png
    plt.plot(rounds, items_collected, '-o', label="Items Collected")
    plt.xlabel("Round")
    plt.ylabel("Total Items Collected")
    plt.title("Items Collected Over Rounds")
    plt.savefig(f'{path_prefix}/{start_time}_items_collected_over_rounds.png', dpi=300)

def save_path_results_png(positions, start_time, path_prefix):

    x_coords = [pos[0] for pos in positions]
    y_coords = [pos[1] for pos in positions]
    z_coords = [pos[2] for pos in positions]

    # 计算总里程数
    total_distance = 0
    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i - 1][0]
        dy = positions[i][1] - positions[i - 1][1]
        dz = positions[i][2] - positions[i - 1][2]
        distance = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        total_distance += distance

    # 3D path png
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(x_coords, y_coords, z_coords, '-o', color='blue', markersize=4)
    ax.set_title("Bot Movement Path in 3D")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.set_zlabel("Z Coordinate")
    ax.text(min(x_coords), max(y_coords), max(z_coords), f"Total Distance: {total_distance:.2f} units", fontsize=15, color='red')
    plt.savefig(f'{path_prefix}/{start_time}_bot_movement_3D_path.png', dpi=300)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze game log file between a start and end time.")
    parser.add_argument('--start_time', type=str, default=None, nargs='?',
                        help="Start time for analysis in the log file.")
    parser.add_argument('--end_time', type=str, default=None, nargs='?', help="End time for analysis in the log file.")
    args = parser.parse_args()


    current_script_path = os.path.dirname(os.path.abspath(__file__))
    filename = f"{current_script_path}/logs/log.txt"

    start_time = None
    if args.start_time:
        # 手动输入起止时间，注意要带上"xxx" 如"2023-10-08 03:14"
        logs_block = extract_logs(filename, args.start_time, args.end_time)
    else:
        # 自动寻找最新的实验开始时间
        start_time = extract_time_from_last_round_zero(filename)
        logs_block = extract_logs(filename, start_time)

    rounds, items_collected, positions = analyze_log_block(logs_block)
    #save png
    save_item_results_png(rounds, items_collected, args.start_time if args.start_time else start_time, current_script_path+"/results_pic")
    save_path_results_png(positions, args.start_time if args.start_time else start_time, current_script_path+"/results_pic")