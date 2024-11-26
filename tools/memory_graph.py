# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt

# 打开并读取文件
file_path = "memory_usage.log"  # 替换为你的文件路径

# 存储提取的所有最后一个数值
last_values = []

# 遍历文件内容并提取最后一个数值
first_line = True
with open(file_path, "r") as file:
    for line in file:
        if first_line:
            first_line = False
            continue
        parts = line.strip().split(",")  # 按逗号分割
        if len(parts) >= 3:
            last_value = float(parts[-1])  # 提取最后一个值
            last_values.append(last_value)  # 保存到列表

# 检查是否成功提取到值
if last_values:
    print(f"提取到的最后一个数值列表: {last_values}")
else:
    print("未找到包含目标数字的行。")

# 如果有提取到值，则绘图
if last_values:
    time_intervals = [i * 5 for i in range(len(last_values))]
    plt.figure(figsize=(10, 6))
    plt.plot(time_intervals, last_values, marker=".", label="Values")
    plt.title("memory usage")
    plt.xlabel("time(s)")
    plt.ylabel("memory(M)")
    plt.grid(True)
    plt.legend()
    plt.show()