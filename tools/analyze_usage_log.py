#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import sys
import matplotlib.dates as mdates
import numpy as np
import os

# 添加matplotlib的Unicode支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']  # 用来正常显示中文
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 添加pandas日期转换器的显式注册，消除警告
try:
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()
except ImportError:
    # 如果是老版本pandas，可能没有这个模块
    pass

def parse_log_file(file_path):
    # 从日志中解析数据
    # Average GC: 从开始到当前时间点的平均GC情况，是累计的平均值
    data = []
    pattern = r'Current: (.*?), PID=(\d+), Memory=(.*?) MB'
    gc_pattern = r'Average GC: YGC=(\d+\.\d+)\((\d+\.\d+)ms\), FGC=(\d+\.\d+)\((\d+\.\d+)ms\)'
    instant_gc_pattern = r'Instant GC: Young GC=(\d+)\((\d+\.\d+)ms\), Full GC=(\d+)\((\d+\.\d+)ms\)'
    avg_pattern = r'Average: Memory=(.*?) MB, CPU=(.*?)%, Threads=(.*?)$'
    raw_gc_pattern = r'Raw GC: Young GC=(\d+), Young GC Time=(\d+\.\d+), Full GC=(\d+), Full GC Time=(\d+\.\d+)'
    
    with open(file_path, 'r') as f:
        content = f.read()
        entries = content.split('--------------------------------------------------------------------------------')
        
        for entry in entries:
            if not entry.strip():
                continue
                
            current_match = re.search(pattern, entry)
            if current_match:
                timestamp = datetime.strptime(current_match.group(1), '%Y-%m-%d %H:%M:%S')
                memory = float(current_match.group(3))
                
                # 默认值，避免某些日志条目缺少特定信息
                ygc_freq = ygc_time = fgc_freq = fgc_time = 0
                avg_memory = avg_cpu = avg_threads = 0
                raw_ygc = raw_ygc_time = raw_fgc = raw_fgc_time = 0
                instant_ygc = instant_ygc_time = instant_fgc = instant_fgc_time = 0
                
                gc_match = re.search(gc_pattern, entry)
                if gc_match:
                    ygc_freq = float(gc_match.group(1))
                    ygc_time = float(gc_match.group(2))
                    fgc_freq = float(gc_match.group(3))
                    fgc_time = float(gc_match.group(4))
                
                instant_gc_match = re.search(instant_gc_pattern, entry)
                if instant_gc_match:
                    instant_ygc = int(instant_gc_match.group(1))
                    instant_ygc_time = float(instant_gc_match.group(2))
                    instant_fgc = int(instant_gc_match.group(3))
                    instant_fgc_time = float(instant_gc_match.group(4))
                
                raw_gc_match = re.search(raw_gc_pattern, entry)
                if raw_gc_match:
                    raw_ygc = int(raw_gc_match.group(1))
                    raw_ygc_time = float(raw_gc_match.group(2))
                    raw_fgc = int(raw_gc_match.group(3))
                    raw_fgc_time = float(raw_gc_match.group(4))
                
                avg_match = re.search(avg_pattern, entry)
                if avg_match:
                    avg_memory = float(avg_match.group(1))
                    avg_cpu = float(avg_match.group(2))
                    avg_threads = float(avg_match.group(3))
                
                # 不管是否找到Average匹配，都添加数据点
                data_point = {
                    'timestamp': timestamp,
                    'memory': memory,
                    'avg_memory': avg_memory,
                    'avg_cpu': avg_cpu,
                    'avg_threads': avg_threads,
                    'ygc_freq': ygc_freq,
                    'ygc_time': ygc_time,
                    'fgc_freq': fgc_freq,
                    'fgc_time': fgc_time,
                    'raw_ygc': raw_ygc,
                    'raw_ygc_time': raw_ygc_time,
                    'raw_fgc': raw_fgc,
                    'raw_fgc_time': raw_fgc_time,
                    'instant_ygc': instant_ygc,
                    'instant_ygc_time': instant_ygc_time,
                    'instant_fgc': instant_fgc,
                    'instant_fgc_time': instant_fgc_time
                }
                data.append(data_point)
    
    print(u"日志数据解析完成，共{}条记录".format(len(data)))
    
    return pd.DataFrame(data)

def analyze_data(df):
    duration = df['timestamp'].max() - df['timestamp'].min()
    hours = duration.total_seconds() / 3600
    
    memory_growth = df['memory'].max() - df['memory'].min()
    hourly_growth = memory_growth / hours if hours > 0 else 0
    
    # 获取最后一行数据
    last_row = df.iloc[-1]
    
    print(u"\n性能分析结果:")
    print(u"-" * 50)
    print(u"运行时长: {}".format(duration))
    print(u"内存总增长: {:.2f} MB".format(memory_growth))
    print(u"平均每小时增长: {:.2f} MB/hour".format(hourly_growth))
    print(u"-" * 50)
    print(u"最终平均GC统计:")
    print(u"Young GC: {:.2f}次/5秒, 平均耗时: {:.2f}ms".format(last_row['ygc_freq'], last_row['ygc_time']))
    print(u"Full GC: {:.2f}次/5秒, 平均耗时: {:.2f}ms".format(last_row['fgc_freq'], last_row['fgc_time']))
    print(u"-" * 50)
    print(u"最终平均资源使用:")
    print(u"内存: {:.2f} MB, CPU: {:.2f}%, 线程数: {:.0f}".format(
        last_row['avg_memory'], last_row['avg_cpu'], last_row['avg_threads']))
    print(u"-" * 50)
    
    return duration, memory_growth, hourly_growth, last_row

def resample_data_by_minute(df):
    """将数据按每分钟重新采样，这样可以避免零值点过多导致的"火焰图"效果"""
    # 设置时间索引
    df_resampled = df.set_index('timestamp')
    
    # 按每分钟重新采样并使用均值填充
    df_resampled = df_resampled.resample('1min').mean()
    
    # 填充缺失值（如果有必要）
    df_resampled = df_resampled.fillna(method='ffill')
    
    # 重置索引，使timestamp重新成为列
    df_resampled = df_resampled.reset_index()
    
    return df_resampled

def calculate_realtime_gc(df):
    """计算实时GC数据，每分钟采样一次"""
    # 复制数据框并添加新列
    df = df.copy()
    
    # 确保数据按时间排序
    df = df.sort_values('timestamp')
    
    # 添加新列用于存储实时GC数据
    df['rt_ygc_freq'] = 0.0
    df['rt_ygc_time'] = 0.0
    df['rt_fgc_freq'] = 0.0
    df['rt_fgc_time'] = 0.0
    
    # 对每个时间点，计算相对于前一分钟的GC变化
    if len(df) > 1:
        for i in range(1, len(df)):
            # 计算时间差（秒）
            time_diff = (df.iloc[i]['timestamp'] - df.iloc[i-1]['timestamp']).total_seconds()
            
            if time_diff > 0:
                # 计算YGC次数和时间变化率（每分钟）
                ygc_diff = df.iloc[i]['raw_ygc'] - df.iloc[i-1]['raw_ygc']
                ygc_time_diff = df.iloc[i]['raw_ygc_time'] - df.iloc[i-1]['raw_ygc_time']
                
                # 计算FGC次数和时间变化率（每分钟）
                fgc_diff = df.iloc[i]['raw_fgc'] - df.iloc[i-1]['raw_fgc']
                fgc_time_diff = df.iloc[i]['raw_fgc_time'] - df.iloc[i-1]['raw_fgc_time']
                
                # 转换为每分钟的频率
                minutes = time_diff / 60
                if minutes > 0:
                    df.loc[df.index[i], 'rt_ygc_freq'] = ygc_diff / minutes
                    df.loc[df.index[i], 'rt_fgc_freq'] = fgc_diff / minutes
                
                # 计算平均每次GC的耗时（毫秒）
                if ygc_diff > 0:
                    df.loc[df.index[i], 'rt_ygc_time'] = (ygc_time_diff * 1000) / ygc_diff
                if fgc_diff > 0:
                    df.loc[df.index[i], 'rt_fgc_time'] = (fgc_time_diff * 1000) / fgc_diff
    
    # 处理首行
    df.loc[df.index[0], 'rt_ygc_freq'] = df.loc[df.index[0], 'ygc_freq']
    df.loc[df.index[0], 'rt_fgc_freq'] = df.loc[df.index[0], 'fgc_freq']
    df.loc[df.index[0], 'rt_ygc_time'] = df.loc[df.index[0], 'ygc_time']
    df.loc[df.index[0], 'rt_fgc_time'] = df.loc[df.index[0], 'fgc_time']
    
    return df

def extract_instant_gc_data(df):
    """每10分钟提取一次实时GC数据"""
    # 复制数据框
    df = df.copy()
    
    # 确保数据按时间排序
    df = df.sort_values('timestamp')
    
    # 获取开始和结束时间
    start_time = df['timestamp'].min()
    end_time = df['timestamp'].max()
    
    # 创建一个新的DataFrame来存储每10分钟的数据点
    ten_min_points = []
    
    # 设置当前时间为开始时间
    current_time = start_time
    
    # 每隔10分钟取一个点
    while current_time <= end_time:
        # 找到最接近当前时间的数据点
        closest_idx = (df['timestamp'] - current_time).abs().idxmin()
        ten_min_points.append(df.loc[closest_idx])
        
        # 增加10分钟
        current_time += timedelta(minutes=10)
    
    # 创建新的DataFrame
    return pd.DataFrame(ten_min_points)

def create_visualizations(df, log_file):
    # 按每分钟重新采样数据
    df_resampled = resample_data_by_minute(df)
    
    # 计算实时GC数据
    df_with_rt = calculate_realtime_gc(df_resampled)
    
    # 获取性能分析结果
    duration = df['timestamp'].max() - df['timestamp'].min()
    hours = duration.total_seconds() / 3600
    memory_growth = df['memory'].max() - df['memory'].min()
    hourly_growth = memory_growth / hours if hours > 0 else 0
    last_row = df.iloc[-1]
    
    # 创建四个图表布局
    fig = plt.figure(figsize=(15, 10))
    
    # 设置时间格式，只显示时分，不显示秒
    time_format = mdates.DateFormatter('%H:%M')
    
    # 第一个图：内存使用趋势
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(df_with_rt['timestamp'], df_with_rt['memory'], label=u'当前内存', color='blue')
    ax1.plot(df_with_rt['timestamp'], df_with_rt['avg_memory'], label=u'平均内存', color='red', linestyle='--')
    ax1.set_title(u'内存使用趋势')
    ax1.set_xlabel(u'时间')
    ax1.set_ylabel(u'内存 (MB)')
    ax1.xaxis.set_major_formatter(time_format)
    ax1.legend()
    ax1.grid(True)
    
    # 第二个图：GC频率
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(df_with_rt['timestamp'], df_with_rt['ygc_freq'], label=u'Young GC频率', color='green')
    ax2.plot(df_with_rt['timestamp'], df_with_rt['fgc_freq'], label=u'Full GC频率', color='red')
    ax2.set_title(u'GC频率')
    ax2.set_xlabel(u'时间')
    ax2.set_ylabel(u'频率 (每5秒)')
    ax2.xaxis.set_major_formatter(time_format)
    ax2.legend()
    ax2.grid(True)
    
    # 第三个图：GC时间
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(df_with_rt['timestamp'], df_with_rt['ygc_time'], label=u'Young GC时间', color='green')
    ax3.plot(df_with_rt['timestamp'], df_with_rt['fgc_time'], label=u'Full GC时间', color='red')
    ax3.set_title(u'GC时间')
    ax3.set_xlabel(u'时间')
    ax3.set_ylabel(u'时间 (ms)')
    ax3.xaxis.set_major_formatter(time_format)
    ax3.legend()
    ax3.grid(True)
    
    # 第四个图：CPU和线程
    ax4 = plt.subplot(2, 2, 4)
    ax4.plot(df_with_rt['timestamp'], df_with_rt['avg_cpu'], label=u'CPU使用率', color='purple')
    ax4_twin = ax4.twinx()
    ax4_twin.plot(df_with_rt['timestamp'], df_with_rt['avg_threads'], label=u'线程数', color='orange')
    ax4.set_title(u'CPU使用率和线程数')
    ax4.set_xlabel(u'时间')
    ax4.set_ylabel(u'CPU使用率 (%)')
    ax4_twin.set_ylabel(u'线程数')
    ax4.xaxis.set_major_formatter(time_format)
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2)
    ax4.grid(True)
    
    # 添加总标题
    plt.suptitle(u'性能分析', fontsize=16)
    
    # 添加性能分析结果文本
    performance_text = (
        u"运行时长: {} | 内存总增长: {:.2f} MB | 平均每小时增长: {:.2f} MB/hour | "
        u"Young GC: {:.2f}次/5秒({:.2f}ms) | Full GC: {:.2f}次/5秒({:.2f}ms) | "
        u"内存: {:.2f} MB | CPU: {:.2f}% | 线程数: {:.0f}"
    ).format(
        duration, memory_growth, hourly_growth,
        last_row['ygc_freq'], last_row['ygc_time'],
        last_row['fgc_freq'], last_row['fgc_time'],
        last_row['avg_memory'], last_row['avg_cpu'], last_row['avg_threads']
    )
    
    # 添加性能分析文本在底部
    fig.text(0.5, 0.01, performance_text, ha='center', fontsize=10)
    
    # 调整布局和间距
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.08)
    
    # 生成基于输入日志文件名的输出文件名
    log_filename = os.path.basename(log_file)
    output_file = os.path.splitext(log_filename)[0] + '_analysis.png'
    
    # 保存图表
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(u"\n图表已保存为: {}".format(output_file))
    
    plt.show()

def main():
    if len(sys.argv) != 2:
        print(u"使用方法: python analyze_gc_log.py <log_file_path>")
        sys.exit(1)
        
    log_file = sys.argv[1]
    
    try:
        print(u"正在分析日志文件: {}".format(log_file))
        df = parse_log_file(log_file)
        duration, memory_growth, hourly_growth, last_row = analyze_data(df)
        create_visualizations(df, log_file)
        
    except IOError:
        print(u"错误: 找不到文件 '{}'".format(log_file))
        sys.exit(1)
    except Exception as e:
        print(u"错误: 分析过程中出现异常: {}".format(str(e)))
        import traceback
        traceback.print_exc()  # 打印详细的错误堆栈
        sys.exit(1)

if __name__ == "__main__":
    main()
