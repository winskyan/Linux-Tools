#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime, timedelta
import matplotlib
import sys
import os

# 根据平台自动选择合适的后端和字体
platform = sys.platform
INTERACTIVE = False

# 直接设置一个基础字体作为备用
BASE_FONT = 'DejaVu Sans'

# 在开始时设置后端，防止被其他库修改
if platform.startswith('linux'):
    matplotlib.use('Agg')
    # 尝试添加字体目录
    os.environ['FONTCONFIG_PATH'] = '/etc/fonts'

# 添加字体检测和优化函数
def get_available_chinese_fonts():
    """检测系统中可用的中文字体"""
    from matplotlib.font_manager import fontManager
    available_fonts = []
    
    # 常见的Linux中文字体
    linux_chinese_fonts = [
        'Noto Sans CJK SC', 'Noto Sans CJK TC', 
        'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
        'Droid Sans Fallback', 'Source Han Sans CN',
        'Source Han Sans TW', 'Source Han Serif CN',
        'AR PL UMing CN', 'AR PL KaitiM GB'
    ]
    
    # 获取所有可用字体的名称
    font_names = [f.name for f in fontManager.ttflist]
    
    # 检查中文字体是否可用
    for font in linux_chinese_fonts:
        if font in font_names:
            available_fonts.append(font)
    
    return available_fonts

# 检查DejaVu Sans字体是否可用
def is_dejavu_available():
    """检查DejaVu Sans字体是否可用"""
    from matplotlib.font_manager import fontManager
    font_names = [f.name for f in fontManager.ttflist]
    return 'DejaVu Sans' in font_names

# 检测操作系统类型并设置相应的配置
if platform.startswith('linux'):
    # Linux环境：使用非交互式后端
    matplotlib.use('Agg')
    # 添加常见的Linux中文字体
    FONT_LIST = [
        'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Droid Sans Fallback',
        'Source Han Sans CN', 'WenQuanYi Zen Hei', 'AR PL UMing CN',
        'DejaVu Sans', 'Liberation Sans', 'FreeSans'
    ]
elif platform == 'darwin':
    # Mac环境：使用交互式后端
    INTERACTIVE = True
    FONT_LIST = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'Helvetica']
else:
    # Windows或其他环境
    FONT_LIST = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    INTERACTIVE = True

import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import numpy as np

# 重置matplotlib字体缓存
try:
    from matplotlib.font_manager import _rebuild
    _rebuild()
except:
    pass

# 尝试检测可用的中文字体并使用
try:
    available_chinese_fonts = get_available_chinese_fonts()
    dejavu_available = is_dejavu_available()
    
    if available_chinese_fonts:
        print(u"检测到可用的中文字体: {}".format(", ".join(available_chinese_fonts[:3])))
        
        if dejavu_available:
            # 确保DejaVu Sans字体在列表中的位置靠前
            FONT_LIST = ['DejaVu Sans'] + available_chinese_fonts + ['Liberation Sans', 'Arial']
            print(u"将使用DejaVu Sans作为主要英文字体")
        else:
            # 如果DejaVu Sans不可用，使用检测到的字体
            FONT_LIST = available_chinese_fonts + ['Liberation Sans', 'Arial', 'FreeSans']
            print(u"警告: DejaVu Sans字体不可用，将使用替代字体")
    else:
        print(u"警告: 未检测到可用的中文字体，图表中的中文可能无法正确显示")
        print(u"建议安装中文字体: sudo apt-get install fonts-noto-cjk fonts-wqy-microhei fonts-wqy-zenhei")
except Exception as e:
    print(u"字体检测过程中出现错误: {}".format(str(e)))

# 确保设置正确的字体配置
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': FONT_LIST,
    'axes.unicode_minus': False,  # 用来正常显示负号
})

# 对于某些版本的matplotlib，需要显式指定默认字体
try:
    # 尝试找一个肯定存在的字体
    import matplotlib.font_manager as fm
    system_fonts = fm.findSystemFonts()
    if system_fonts:
        default_font = fm.FontProperties(fname=system_fonts[0])
        plt.rcParams['font.sans-serif'] = [default_font.get_name()] + FONT_LIST
except:
    pass

# 尝试解决Linux环境下的中文绘图问题
if platform.startswith('linux'):
    # 如果没有找到中文字体，使用fontconfig配置
    if not available_chinese_fonts:
        # 增加设置一个更全面的字体配置
        try:
            # 使用matplotlib的内置配置
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'FreeSans', 'Liberation Sans'] + FONT_LIST
            # 如果matplotlib版本支持fallback字体设置
            if 'fallback_font' in plt.rcParams:
                plt.rcParams['fallback_font'] = 'DejaVu Sans'
        except Exception as e:
            print(u"字体设置过程中出现错误: {}".format(str(e)))
            
    # 尝试另一种方式加载字体
    try:
        from matplotlib import font_manager
        # 添加系统字体路径
        for font_dir in ['/usr/share/fonts/', '/usr/local/share/fonts/']:
            if os.path.exists(font_dir):
                # 尝试使用正确的方法加载字体目录
                try:
                    # 新版matplotlib
                    font_manager.fontManager.addfont(font_dir)
                except AttributeError:
                    # 旧版matplotlib
                    font_files = font_manager.findSystemFonts(fontpaths=[font_dir])
                    for font_file in font_files:
                        font_manager.fontManager.addfont(font_file)
    except Exception:
        pass  # 忽略可能的错误

# 防止字体警告干扰输出
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

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
    
    print("Log data parsing completed, {} records in total".format(len(data)))
    
    return pd.DataFrame(data)

def analyze_data(df):
    duration = df['timestamp'].max() - df['timestamp'].min()
    hours = duration.total_seconds() / 3600
    
    memory_growth = df['memory'].max() - df['memory'].min()
    hourly_growth = memory_growth / hours if hours > 0 else 0
    
    # 获取最后一行数据
    last_row = df.iloc[-1]
    
    print("\nPerformance Analysis Results:")
    print(u"-" * 50)
    print("Duration: {}".format(duration))
    print("Total Memory Growth: {:.2f} MB".format(memory_growth))
    print("Average Hourly Growth: {:.2f} MB/hour".format(hourly_growth))
    print(u"-" * 50)
    print("Final Average GC Statistics:")
    print("Young GC: {:.2f}/5s, Average Time: {:.2f}ms".format(last_row['ygc_freq'], last_row['ygc_time']))
    print("Full GC: {:.2f}/5s, Average Time: {:.2f}ms".format(last_row['fgc_freq'], last_row['fgc_time']))
    print(u"-" * 50)
    print("Final Average Resource Usage:")
    print("Memory: {:.2f} MB, CPU: {:.2f}%, Threads: {:.0f}".format(
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
    
    # 解决英文字体显示问题
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': FONT_LIST,
        'axes.unicode_minus': False,
    })
    
    # 创建四个图表布局
    fig = plt.figure(figsize=(15, 10))
    
    # 设置时间格式，只显示时分，不显示秒
    time_format = mdates.DateFormatter('%H:%M')
    
    # 使用纯英文标签
    memory_title = 'Memory Usage Trend'
    gc_freq_title = 'GC Frequency'
    gc_time_title = 'GC Time'
    cpu_title = 'CPU Usage & Thread Count'
    
    time_label = 'Time'
    memory_label = 'Memory (MB)'
    freq_label = 'Frequency (/5s)'
    time_ms_label = 'Time (ms)'
    cpu_label = 'CPU Usage (%)'
    thread_label = 'Thread Count'
    
    current_mem_label = 'Current Memory'
    avg_mem_label = 'Average Memory'
    ygc_freq_label = 'Young GC Frequency'
    fgc_freq_label = 'Full GC Frequency'
    ygc_time_label = 'Young GC Time'
    fgc_time_label = 'Full GC Time'
    cpu_usage_label = 'CPU Usage'
    thread_count_label = 'Thread Count'
    
    # 第一个图：内存使用趋势
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(df_with_rt['timestamp'], df_with_rt['memory'], label=current_mem_label, color='blue')
    ax1.plot(df_with_rt['timestamp'], df_with_rt['avg_memory'], label=avg_mem_label, color='red', linestyle='--')
    ax1.set_title(memory_title)
    ax1.set_xlabel(time_label)
    ax1.set_ylabel(memory_label)
    ax1.xaxis.set_major_formatter(time_format)
    ax1.legend()
    ax1.grid(True)
    
    # 第二个图：GC频率
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(df_with_rt['timestamp'], df_with_rt['ygc_freq'], label=ygc_freq_label, color='green')
    ax2.plot(df_with_rt['timestamp'], df_with_rt['fgc_freq'], label=fgc_freq_label, color='red')
    ax2.set_title(gc_freq_title)
    ax2.set_xlabel(time_label)
    ax2.set_ylabel(freq_label)
    ax2.xaxis.set_major_formatter(time_format)
    ax2.legend()
    ax2.grid(True)
    
    # 第三个图：GC时间
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(df_with_rt['timestamp'], df_with_rt['ygc_time'], label=ygc_time_label, color='green')
    ax3.plot(df_with_rt['timestamp'], df_with_rt['fgc_time'], label=fgc_time_label, color='red')
    ax3.set_title(gc_time_title)
    ax3.set_xlabel(time_label)
    ax3.set_ylabel(time_ms_label)
    ax3.xaxis.set_major_formatter(time_format)
    ax3.legend()
    ax3.grid(True)
    
    # 第四个图：CPU和线程
    ax4 = plt.subplot(2, 2, 4)
    ax4.plot(df_with_rt['timestamp'], df_with_rt['avg_cpu'], label=cpu_usage_label, color='purple')
    ax4_twin = ax4.twinx()
    ax4_twin.plot(df_with_rt['timestamp'], df_with_rt['avg_threads'], label=thread_count_label, color='orange')
    ax4.set_title(cpu_title)
    ax4.set_xlabel(time_label)
    ax4.set_ylabel(cpu_label)
    ax4_twin.set_ylabel(thread_label)
    ax4.xaxis.set_major_formatter(time_format)
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2)
    ax4.grid(True)
    
    # 添加总标题
    plt.suptitle('Performance Analysis', fontsize=16)
    
    # 添加性能分析结果文本
    performance_text = (
        "Duration: {} | Memory Growth: {:.2f} MB | Hourly Growth: {:.2f} MB/hour | "
        "Young GC: {:.2f}/5s ({:.2f}ms) | Full GC: {:.2f}/5s ({:.2f}ms) | "
        "Memory: {:.2f} MB | CPU: {:.2f}% | Threads: {:.0f}"
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
    output_file = os.path.splitext(log_filename)[0] + '-analysis.png'
    
    # 保存图表
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print("\nChart saved as: {}".format(output_file))
    
    # 根据平台决定是否显示图表
    if INTERACTIVE:
        try:
            plt.show()
        except Exception as e:
            print("Failed to display chart: {}".format(str(e)))
            print("However, chart was successfully saved and can be viewed directly")
    else:
        print("In current environment (Linux), chart is not displayed. Please view the saved image file directly")
        plt.close()

def test_fonts(font_list=None):
    """测试系统中可用的字体并生成示例图片
    
    Args:
        font_list: 指定测试的字体列表，默认测试系统中所有字体
    """
    try:
        from matplotlib.font_manager import FontManager
        import matplotlib.pyplot as plt
        
        # 获取所有可用字体
        font_manager = FontManager()
        font_list = sorted([f.name for f in font_manager.ttflist])
        
        print("Detected {} fonts in the system".format(len(font_list)))
        
        # 创建更详细的测试图表
        fig, axes = plt.subplots(2, 1, figsize=(15, 12))
        
        # 顶部图表：测试中英文和数字混合
        axes[0].set_title('Text and Number Display Test', fontsize=16)
        axes[0].set_xlim(0, 1)
        axes[0].set_ylim(0, 10)
        axes[0].text(0.5, 8, 'Text Display Test 123456789', 
                    fontsize=16, ha='center')
        axes[0].text(0.5, 6, 'CPU Usage and Memory: 50% and 1024MB', 
                    fontsize=16, ha='center')
        axes[0].text(0.5, 4, 'Young GC: 10/sec (10ms)', 
                    fontsize=16, ha='center')
        axes[0].text(0.5, 2, 'Full GC: 1/min (100ms)', 
                    fontsize=16, ha='center')
        axes[0].grid(False)
        axes[0].set_xticks([])
        axes[0].set_yticks([])
        
        # 底部图表：测试简单图表
        x = np.arange(10)
        y1 = x * x
        y2 = x * 10
        
        axes[1].plot(x, y1, 'r-', label='Quadratic Function y=x²')
        axes[1].plot(x, y2, 'b--', label='Linear Function y=10x')
        axes[1].set_title('Plot Test', fontsize=16)
        axes[1].set_xlabel('X-Axis')
        axes[1].set_ylabel('Y-Axis')
        axes[1].legend()
        axes[1].grid(True)
        
        plt.suptitle('Font and Plot Test', fontsize=20)
        
        plt.savefig('font_test.png')
        print("\nFont test result saved to: font_test.png")
        print("Please check the image to confirm all text and numbers display correctly")
    except Exception as e:
        print("Font test failed: {}".format(str(e)))
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_usage_log.py <log_file_path>")
        print("       python analyze_usage_log.py test-fonts  # Test system fonts")
        sys.exit(1)
        
    log_file = sys.argv[1]
    
    # 添加字体测试功能
    if log_file == 'test-fonts':
        test_fonts()
        return
    
    try:
        print("Analyzing log file: {}".format(log_file))
        df = parse_log_file(log_file)
        duration, memory_growth, hourly_growth, last_row = analyze_data(df)
        create_visualizations(df, log_file)
        
    except IOError:
        print("Error: File not found '{}'".format(log_file))
        sys.exit(1)
    except Exception as e:
        print("Error: Exception during analysis: {}".format(str(e)))
        import traceback
        traceback.print_exc()  # 打印详细的错误堆栈
        # 字体相关错误处理
        if "font" in str(e).lower():
            print("\nTip: Font issues detected, please try the following solutions:")
            print("1. Install more fonts:")
            print("   Ubuntu/Debian: sudo apt-get install fonts-dejavu fonts-liberation")
            print("   CentOS/RHEL:   sudo yum install dejavu-sans-fonts liberation-fonts")
            print("2. Run font test: python analyze_usage_log.py test-fonts")
            print("3. If needed, manually install more fonts:")
            print("   sudo mkdir -p /usr/share/fonts/truetype/custom")
            print("   sudo cp your_font.ttf /usr/share/fonts/truetype/custom/")
            print("   sudo fc-cache -fv")
        # 显示相关错误
        elif "display" in str(e).lower():
            print("\nTip: This is a graphical interface error, but the chart should have been saved as an image file")
        sys.exit(1)

if __name__ == "__main__":
    main()
