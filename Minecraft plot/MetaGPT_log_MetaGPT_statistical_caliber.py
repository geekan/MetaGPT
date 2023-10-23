import re
import argparse
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import numpy as np
import random
import seaborn as sns
import matplotlib as mpl
import pandas as pd
mpl.rcParams.update(mpl.rcParamsDefault)

def extract_logs(filename, start_time=None, end_time=None):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if start_time is None :
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
        if end_time and end_time in line:
            capture = False
            break

    return logs_block

def extract_time_from_first_round_zero(log_filename):
    with open(log_filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 正向遍历文件的每一行
    for line in lines:
        if "Config loading done" in line:
            # 正则表达式匹配年月日 小时:分钟的格式
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
            if match:
                return match.group(1)
    return None

def analyze_log_block(logs_block):
    rounds: list[int] = []
    items_collected :list[int] = []
    total_items = 0
    positions:list[(int, int, int)] = []
    completed_tasks: list[int] = []
    failed_tasks: list[int] = []
    items_variety_collected :list[int] = []
    items_collected_dict :list[dict] = []
    biomes: list[str] = []  # 存储所有出现过的生物群系
    biomes_per_round: list[list[str]] = []  # 存储每轮结束时已经经历过的生物群系
    new_biome_rounds: list[int] = []  # 存储添加新生物群系的轮次
    round_start = False
    check_for_info = False  
    line_after_message = 0  
    first_group = True  


    for line in logs_block:
        if "round_id:" in line:
            n = int(re.search(r'round_id:(\d+)', line).group(1))
            if n not in rounds:
                rounds.append(n)
                round_start = True

        if round_start:
            if "Curriculum Agent human message" in line:
                if check_for_info:  # 如果已经开始解析，就跳过这一轮的剩余部分
                    round_start = False
                    continue
                check_for_info = True
                line_after_message = 0
                continue

            if check_for_info:
                line_after_message += 1

                if line_after_message <= 100:
                    if "Position: x=" in line:
                        match = re.search(r'Position: x=([\d.-]+), y=([\d.-]+), z=([\d.-]+)', line)
                        x, y, z = float(match.group(1)), float(match.group(2)), float(match.group(3))
                        positions.append((x, y, z))

                    if "Inventory (" in line:
                        if ": Empty" in line:
                            items_collected.append(0)
                            items = None
                            items_collected_dict.append({})  # 将这一轮结束时的物品存储状态添加到列表中
                            total_items = 0
                            items_variety_collected.append(0)  # 统计物品种类数量
                        else:
                            items = re.search(r'Inventory \(\d+/36\): ({.*?})', line).group(1)
                            items_dict = eval(items)
                            items_collected_dict.append(items_dict)  # 将这一轮结束时的物品存储状态添加到列表中
                            total_items = sum(items_dict.values())
                            items_collected.append(total_items)
                            items_variety_collected.append(len(items_dict))  # 统计物品种类数量
                    if "Biome: " in line:  
                        biome = line.replace("Biome: ", "").strip()
                        if biome not in biomes:
                            biomes.append(biome)
                            new_biome_rounds.append(rounds[-1])  # 记录添加新生物群系的轮次
                        biomes_per_round.append(biomes.copy())  # 记录当前已经经历过
                    if "Completed tasks so far:" in line:
                        tasks = line.replace("Completed tasks so far:", "").strip().split("; ")
                        completed_tasks.append(0 if tasks == ['None'] else len(tasks))

                    if "Failed tasks that are too hard:" in line:
                        tasks = line.replace("Failed tasks that are too hard:", "").strip().split("; ")
                        failed_tasks.append(0 if tasks == ['None'] else len(tasks))
                        check_for_info = False
                        round_start = False
                    if "metagpt.actions.minecraft.design_curriculumn" in line:
                        check_for_info = False
                        round_start = False
    min_len: int = min(len(rounds), len(items_collected), len(positions), len(completed_tasks), len(failed_tasks))
    return rounds[:min_len], items_collected[:min_len], items_variety_collected[:min_len], items_collected_dict[:min_len], positions[:min_len], completed_tasks[:min_len], failed_tasks[:min_len], biomes, biomes_per_round[:min_len], new_biome_rounds


def save_item_results_png(rounds, items_collected, items_collected_dict, start_time, path_prefix):
    items_collected_total = {}
    items_collected_total_list = []
    for round_index in range(len(rounds)):
        for item, quantity in items_collected_dict[round_index].items():
            if item in items_collected_total:
                items_collected_total[item] = max(items_collected_total[item], quantity)
            else:
                items_collected_total[item] = quantity
        items_collected_total_list.append(sum(items_collected_total.values()))
    print("总数",items_collected_total_list)
    plt.figure(figsize=(10, 5))
    plt.plot(rounds, items_collected_total_list,  label="Items Collected")
    plt.xlabel("# of Rounds")
    plt.ylabel("Total Items Collected")
    plt.title("Items Collected Over Rounds")
    plt.grid(True)
    plt.legend()

    ax = plt.gca()

    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    ax.grid(color='gray', linestyle='-', linewidth=0.3, alpha=0.2)

    # 设置x轴和y轴的箭头
    ax.annotate('', xy=(1, 0), xycoords='axes fraction', xytext=(0, 0), 
                arrowprops=dict(arrowstyle="->", color='black'))
    ax.annotate('', xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), 
                arrowprops=dict(arrowstyle="->", color='black'))
    
    plt.savefig(f'{path_prefix}/{start_time}_items_collected_over_rounds.png', dpi=300)
    plt.close()

    # 物品种类数量png
    plt.figure(figsize=(10, 5))
    plt.xlabel("# of Rounds")
    plt.ylabel("Total Variety of Items Collected")
    plt.title("Variety of Items Collected Over Rounds")
    plt.grid(True)

    special_items = ['oak_log', 'spruce_log', 'birch_log', 'jungle_log', 'dark_oak_log', 'acacia_log', 'stick', 'crafting_table', 'wooden_pickaxe', 'cobblestone', 'stone_pickaxe', 'coal', 'charcoal', 'furnace', 'blast_furnace', 'iron_ore', 'iron_ingot', 'iron_pickaxe', 'diamond', 'diamond_sword', 'diamond_pickaxe', 'diamond_axe', 'diamond_shovel', 'diamond_hoe', 'diamond_helmet', 'diamond_chestplate', 'diamond_leggings', 'diamond_boots']

    collected_items_set = set()
    items_variety_collected = []

    for i in range(0, len(items_collected_dict)):
        current_round_items_set = set(items_collected_dict[i])
        diff_items = list(current_round_items_set - collected_items_set)
        collected_items_set.update(current_round_items_set)
        items_variety_collected.append(len(collected_items_set))
        if diff_items and False:
            for j, item in enumerate(diff_items):
                # 判断物品类型，选择不同的背景颜色
                if item in special_items:
                    color = 'black'
                    bgcolor = 'orange'

                else :
                    color = 'black'
                    bgcolor = 'green'
                # 避免文字重叠，通过调整 y 坐标的值
                y = items_variety_collected[i]-1-1*j
                plt.text(rounds[i], y, item, fontsize=4, color=color, ha='center', va='top',
                         bbox=dict(boxstyle='round,pad=0.5', fc=bgcolor, alpha=0.5))
                    
    
    plt.plot(rounds, items_variety_collected, label="Variety of Items Collected")
    plt.legend()
    
    ax = plt.gca()

    # 设置坐标显示为整数
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # 移除所有边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # 设置网格线颜色和透明度
    ax.grid(color='gray', linestyle='-', linewidth=0.3, alpha=0.2)

    # 设置x轴和y轴的箭头
    ax.annotate('', xy=(1, 0), xycoords='axes fraction', xytext=(0, 0), 
                arrowprops=dict(arrowstyle="->", color='black'))
    ax.annotate('', xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), 
                arrowprops=dict(arrowstyle="->", color='black'))
    
    plt.savefig(f'{path_prefix}/{start_time}_variety_items_collected_over_rounds.png', dpi=600)
    plt.close()

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
    ax.plot(x_coords[0], y_coords[0], z_coords[0], 'ro')  # start point with red color
    ax.plot(x_coords[-1], y_coords[-1], z_coords[-1], 'go')  # end point with green color
    
    plt.savefig(f'{path_prefix}/{start_time}_bot_movement_3D_path.png', dpi=300)
    plt.close()

def save_task_results_png(rounds , completed, failed, start_time, path_prefix):
    plt.plot(rounds, completed, label='Completed Tasks')
    plt.plot(rounds, failed, label='Failed Tasks')

    plt.xlabel("# of Rounds")
    plt.ylabel("Number of Tasks")
    plt.title("Completed vs Failed Tasks per Round")
    plt.legend()

    ax = plt.gca()

    # 设置坐标显示为整数
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # 移除所有边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # 设置网格线颜色和透明度
    ax.grid(color='gray', linestyle='-', linewidth=0.3, alpha=0.2)

    # 设置x轴和y轴的箭头
    ax.annotate('', xy=(1, 0), xycoords='axes fraction', xytext=(0, 0), 
                arrowprops=dict(arrowstyle="->", color='black'))
    ax.annotate('', xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), 
                arrowprops=dict(arrowstyle="->", color='black'))

    plt.savefig(f'{path_prefix}/{start_time}_task_results.png', dpi=300)
    plt.close()

def main():

    # 获取当前脚本的路径
    current_script_path = os.path.dirname(os.path.abspath(__file__))

    # 构建其他文件的路径
    filename = os.path.join(current_script_path, 'input', 'MG-1.txt')
    path_prefix = os.path.join(current_script_path, 'results_pic')

    # 确保输出路径存在
    os.makedirs(path_prefix, exist_ok=True)

    # 自动寻找最新的实验开始时间
    start_time = extract_time_from_first_round_zero(filename)
    logs_block = extract_logs(filename, start_time)

    rounds, items_collected, items_variety_collected, items_collected_dict, positions, completed_tasks, failed_tasks, biomes, biomes_per_round, new_biome_rounds = analyze_log_block(logs_block)


    collected_items_set = set()
    total_items_variety = []
    for i in range(0, len(items_collected_dict)):
        current_round_items_set = set(items_collected_dict[i])
        collected_items_set.update(current_round_items_set)
        total_items_variety.append(len(collected_items_set))
    
    #save png
    start_time = start_time.replace(":", "_")
    save_item_results_png(rounds, items_collected, items_collected_dict, start_time, path_prefix)
    save_path_results_png(positions, start_time, path_prefix)
    save_task_results_png(rounds, completed_tasks, failed_tasks, start_time, path_prefix)
    #save_item_results_png(rounds, items_collected, items_variety_collected, items_collected_dict, start_time, path_prefix)
    print("种类",total_items_variety)
    print("轮次", rounds)
    print("总数",items_collected)
    print("成功",completed_tasks)
    print("失败",failed_tasks)
    print("位置",positions)
    
    data = {'rounds': rounds,
            'items_collected': items_collected,
            'total_items_variety':total_items_variety,
            'items_variety_collected': items_collected_dict,
            'positions': positions,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks}
    # 创建一个DataFrame
    df = pd.DataFrame(data)
    # 创建一个新的DataFrame，存储new_biome_rounds和biomes
    df_new_biomes = pd.DataFrame({
        'new_biome_rounds': new_biome_rounds,
        'biomes': biomes
    })
    # 将新的DataFrame和原来的df进行合并
    df = pd.concat([df, df_new_biomes], axis=1)

    # 写入到Excel文件中
    df.to_excel(os.path.join(path_prefix, f'{start_time}_results.xlsx'), index=False)
if __name__ == "__main__":
    main()
