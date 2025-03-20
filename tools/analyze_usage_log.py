#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime, timedelta
import matplotlib
import sys
import os

# Automatically select appropriate backend and font based on platform
platform = sys.platform
INTERACTIVE = False

# Set a basic font as fallback
BASE_FONT = 'DejaVu Sans'

# Set backend at the beginning to prevent modification by other libraries
if platform.startswith('linux'):
    matplotlib.use('Agg')
    # Try to add font directory
    os.environ['FONTCONFIG_PATH'] = '/etc/fonts'

# Add font detection and optimization functions
def get_available_chinese_fonts():
    """Detect available Chinese fonts in the system"""
    from matplotlib.font_manager import fontManager
    available_fonts = []
    
    # Common Linux Chinese fonts
    linux_chinese_fonts = [
        'Noto Sans CJK SC', 'Noto Sans CJK TC', 
        'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
        'Droid Sans Fallback', 'Source Han Sans CN',
        'Source Han Sans TW', 'Source Han Serif CN',
        'AR PL UMing CN', 'AR PL KaitiM GB'
    ]
    
    # Get names of all available fonts
    font_names = [f.name for f in fontManager.ttflist]
    
    # Check if Chinese fonts are available
    for font in linux_chinese_fonts:
        if font in font_names:
            available_fonts.append(font)
    
    return available_fonts

# Check if DejaVu Sans font is available
def is_dejavu_available():
    """Check if DejaVu Sans font is available"""
    from matplotlib.font_manager import fontManager
    font_names = [f.name for f in fontManager.ttflist]
    return 'DejaVu Sans' in font_names

# Detect OS type and set appropriate configuration
if platform.startswith('linux'):
    # Linux environment: use non-interactive backend
    matplotlib.use('Agg')
    # Add common Linux Chinese fonts
    FONT_LIST = [
        'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Droid Sans Fallback',
        'Source Han Sans CN', 'WenQuanYi Zen Hei', 'AR PL UMing CN',
        'DejaVu Sans', 'Liberation Sans', 'FreeSans'
    ]
elif platform == 'darwin':
    # Mac environment: use interactive backend
    INTERACTIVE = True
    FONT_LIST = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'Helvetica']
else:
    # Windows or other environments
    FONT_LIST = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    INTERACTIVE = True

import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import numpy as np

# Reset matplotlib font cache
try:
    from matplotlib.font_manager import _rebuild
    _rebuild()
except:
    pass

# Try to detect available Chinese fonts and use them
try:
    available_chinese_fonts = get_available_chinese_fonts()
    dejavu_available = is_dejavu_available()
    
    if available_chinese_fonts:
        print("Detected available Chinese fonts: {}".format(", ".join(available_chinese_fonts[:3])))
        
        if dejavu_available:
            # Ensure DejaVu Sans font is positioned at the front of the list
            FONT_LIST = ['DejaVu Sans'] + available_chinese_fonts + ['Liberation Sans', 'Arial']
            print("Will use DejaVu Sans as the main English font")
        else:
            # If DejaVu Sans is not available, use detected fonts
            FONT_LIST = available_chinese_fonts + ['Liberation Sans', 'Arial', 'FreeSans']
            print("Warning: DejaVu Sans font is not available, will use alternative fonts")
    else:
        print("Warning: No available Chinese fonts detected, Chinese characters may not display correctly")
        print("Suggestion: Install Chinese fonts: sudo apt-get install fonts-noto-cjk fonts-wqy-microhei fonts-wqy-zenhei")
except Exception as e:
    print("Error during font detection: {}".format(str(e)))

# Ensure correct font configuration
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': FONT_LIST,
    'axes.unicode_minus': False,  # For correct display of minus sign
})

# For some versions of matplotlib, need to explicitly specify default font
try:
    # Try to find a font that definitely exists
    import matplotlib.font_manager as fm
    system_fonts = fm.findSystemFonts()
    if system_fonts:
        default_font = fm.FontProperties(fname=system_fonts[0])
        plt.rcParams['font.sans-serif'] = [default_font.get_name()] + FONT_LIST
except:
    pass

# Try to solve Chinese plotting issues in Linux environment
if platform.startswith('linux'):
    # If no Chinese fonts found, use fontconfig configuration
    if not available_chinese_fonts:
        # Set a more comprehensive font configuration
        try:
            # Use matplotlib's built-in configuration
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'FreeSans', 'Liberation Sans'] + FONT_LIST
            # If matplotlib version supports fallback font setting
            if 'fallback_font' in plt.rcParams:
                plt.rcParams['fallback_font'] = 'DejaVu Sans'
        except Exception as e:
            print("Error during font setting: {}".format(str(e)))
            
    # Try another way to load fonts
    try:
        from matplotlib import font_manager
        # Add system font paths
        for font_dir in ['/usr/share/fonts/', '/usr/local/share/fonts/']:
            if os.path.exists(font_dir):
                # Try to use the correct method to load font directory
                try:
                    # New version of matplotlib
                    font_manager.fontManager.addfont(font_dir)
                except AttributeError:
                    # Old version of matplotlib
                    font_files = font_manager.findSystemFonts(fontpaths=[font_dir])
                    for font_file in font_files:
                        font_manager.fontManager.addfont(font_file)
    except Exception:
        pass  # Ignore possible errors

# Prevent font warnings from interfering with output
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# Add explicit registration of pandas date converters to eliminate warnings
try:
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()
except ImportError:
    # For older versions of pandas, this module might not exist
    pass

def parse_log_file(file_path):
    # Parse data from log
    # Average GC: cumulative average GC from start to current time point
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
                
                # Default values to avoid missing specific information in some log entries
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
                
                # Add data point regardless of whether Average match is found
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
    
    # Get the last row of data
    last_row = df.iloc[-1]
    
    print("\nPerformance Analysis Results:")
    print("-" * 50)
    print("Duration: {}".format(duration))
    print("Total Memory Growth: {:.2f} MB".format(memory_growth))
    print("Average Hourly Growth: {:.2f} MB/hour".format(hourly_growth))
    print("-" * 50)
    print("Final Average GC Statistics:")
    print("Young GC: {:.2f}/5s, Average Time: {:.2f}ms".format(last_row['ygc_freq'], last_row['ygc_time']))
    print("Full GC: {:.2f}/5s, Average Time: {:.2f}ms".format(last_row['fgc_freq'], last_row['fgc_time']))
    print("-" * 50)
    print("Final Average Resource Usage:")
    print("Memory: {:.2f} MB, CPU: {:.2f}%, Threads: {:.0f}".format(
        last_row['avg_memory'], last_row['avg_cpu'], last_row['avg_threads']))
    print("-" * 50)
    
    return duration, memory_growth, hourly_growth, last_row

def resample_data_by_minute(df):
    """Resample data by minute to avoid 'flame graph' effect caused by too many zero value points"""
    # Set time index
    df_resampled = df.set_index('timestamp')
    
    # Resample by minute and fill with mean values
    df_resampled = df_resampled.resample('1min').mean()
    
    # Fill missing values (if necessary)
    df_resampled = df_resampled.fillna(method='ffill')
    
    # Reset index to make timestamp a column again
    df_resampled = df_resampled.reset_index()
    
    return df_resampled

def calculate_realtime_gc(df):
    """Calculate real-time GC data, sampled once per minute"""
    # Copy dataframe and add new columns
    df = df.copy()
    
    # Ensure data is sorted by time
    df = df.sort_values('timestamp')
    
    # Add new columns for real-time GC data
    df['rt_ygc_freq'] = 0.0
    df['rt_ygc_time'] = 0.0
    df['rt_fgc_freq'] = 0.0
    df['rt_fgc_time'] = 0.0
    
    # For each time point, calculate GC changes relative to the previous minute
    if len(df) > 1:
        for i in range(1, len(df)):
            # Calculate time difference (seconds)
            time_diff = (df.iloc[i]['timestamp'] - df.iloc[i-1]['timestamp']).total_seconds()
            
            if time_diff > 0:
                # Calculate YGC count and time change rate (per minute)
                ygc_diff = df.iloc[i]['raw_ygc'] - df.iloc[i-1]['raw_ygc']
                ygc_time_diff = df.iloc[i]['raw_ygc_time'] - df.iloc[i-1]['raw_ygc_time']
                
                # Calculate FGC count and time change rate (per minute)
                fgc_diff = df.iloc[i]['raw_fgc'] - df.iloc[i-1]['raw_fgc']
                fgc_time_diff = df.iloc[i]['raw_fgc_time'] - df.iloc[i-1]['raw_fgc_time']
                
                # Convert to frequency per minute
                minutes = time_diff / 60
                if minutes > 0:
                    df.loc[df.index[i], 'rt_ygc_freq'] = ygc_diff / minutes
                    df.loc[df.index[i], 'rt_fgc_freq'] = fgc_diff / minutes
                
                # Calculate average time per GC (milliseconds)
                if ygc_diff > 0:
                    df.loc[df.index[i], 'rt_ygc_time'] = (ygc_time_diff * 1000) / ygc_diff
                if fgc_diff > 0:
                    df.loc[df.index[i], 'rt_fgc_time'] = (fgc_time_diff * 1000) / fgc_diff
    
    # Process first row
    df.loc[df.index[0], 'rt_ygc_freq'] = df.loc[df.index[0], 'ygc_freq']
    df.loc[df.index[0], 'rt_fgc_freq'] = df.loc[df.index[0], 'fgc_freq']
    df.loc[df.index[0], 'rt_ygc_time'] = df.loc[df.index[0], 'ygc_time']
    df.loc[df.index[0], 'rt_fgc_time'] = df.loc[df.index[0], 'fgc_time']
    
    return df

def extract_instant_gc_data(df):
    """Extract real-time GC data every 10 minutes"""
    # Copy dataframe
    df = df.copy()
    
    # Ensure data is sorted by time
    df = df.sort_values('timestamp')
    
    # Get start and end times
    start_time = df['timestamp'].min()
    end_time = df['timestamp'].max()
    
    # Create a new DataFrame to store data points every 10 minutes
    ten_min_points = []
    
    # Set current time to start time
    current_time = start_time
    
    # Take a point every 10 minutes
    while current_time <= end_time:
        # Find the data point closest to current time
        closest_idx = (df['timestamp'] - current_time).abs().idxmin()
        ten_min_points.append(df.loc[closest_idx])
        
        # Add 10 minutes
        current_time += timedelta(minutes=10)
    
    # Create new DataFrame
    return pd.DataFrame(ten_min_points)

def create_visualizations(df, log_file):
    # Resample data by minute
    df_resampled = resample_data_by_minute(df)
    
    # Calculate real-time GC data
    df_with_rt = calculate_realtime_gc(df_resampled)
    
    # Get performance analysis results
    duration = df['timestamp'].max() - df['timestamp'].min()
    hours = duration.total_seconds() / 3600
    memory_growth = df['memory'].max() - df['memory'].min()
    hourly_growth = memory_growth / hours if hours > 0 else 0
    last_row = df.iloc[-1]
    
    # Solve English font display issues
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': FONT_LIST,
        'axes.unicode_minus': False,
    })
    
    # Create four chart layout
    fig = plt.figure(figsize=(15, 10))
    
    # Set time format to show only hours and minutes, not seconds
    time_format = mdates.DateFormatter('%H:%M')
    
    # Use English-only labels
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
    
    # First chart: Memory usage trend
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(df_with_rt['timestamp'], df_with_rt['memory'], label=current_mem_label, color='blue')
    ax1.plot(df_with_rt['timestamp'], df_with_rt['avg_memory'], label=avg_mem_label, color='red', linestyle='--')
    ax1.set_title(memory_title)
    ax1.set_xlabel(time_label)
    ax1.set_ylabel(memory_label)
    ax1.xaxis.set_major_formatter(time_format)
    ax1.legend()
    ax1.grid(True)
    
    # Second chart: GC frequency
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(df_with_rt['timestamp'], df_with_rt['ygc_freq'], label=ygc_freq_label, color='green')
    ax2.plot(df_with_rt['timestamp'], df_with_rt['fgc_freq'], label=fgc_freq_label, color='red')
    ax2.set_title(gc_freq_title)
    ax2.set_xlabel(time_label)
    ax2.set_ylabel(freq_label)
    ax2.xaxis.set_major_formatter(time_format)
    ax2.legend()
    ax2.grid(True)
    
    # Third chart: GC time
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(df_with_rt['timestamp'], df_with_rt['ygc_time'], label=ygc_time_label, color='green')
    ax3.plot(df_with_rt['timestamp'], df_with_rt['fgc_time'], label=fgc_time_label, color='red')
    ax3.set_title(gc_time_title)
    ax3.set_xlabel(time_label)
    ax3.set_ylabel(time_ms_label)
    ax3.xaxis.set_major_formatter(time_format)
    ax3.legend()
    ax3.grid(True)
    
    # Fourth chart: CPU and threads
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
    
    # Add overall title
    plt.suptitle('Performance Analysis', fontsize=16)
    
    # Add performance analysis results text
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
    
    # Add performance analysis text at the bottom
    fig.text(0.5, 0.01, performance_text, ha='center', fontsize=10)
    
    # Adjust layout and spacing
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.08)
    
    # Generate output filename based on input log filename
    log_filename = os.path.basename(log_file)
    output_file = os.path.splitext(log_filename)[0] + '-analysis.png'
    
    # Save chart
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print("\nChart saved as: {}".format(output_file))
    
    # Decide whether to display chart based on platform
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
    """Test available fonts in the system and generate sample image
    
    Args:
        font_list: Specified list of fonts to test, defaults to testing all system fonts
    """
    try:
        from matplotlib.font_manager import FontManager
        import matplotlib.pyplot as plt
        
        # Get all available fonts
        font_manager = FontManager()
        font_list = sorted([f.name for f in font_manager.ttflist])
        
        print("Detected {} fonts in the system".format(len(font_list)))
        
        # Create more detailed test chart
        fig, axes = plt.subplots(2, 1, figsize=(15, 12))
        
        # Top chart: Test mixed English and numbers
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
        
        # Bottom chart: Test simple chart
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
    
    # Add font testing functionality
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
        traceback.print_exc()  # Print detailed error stack
        # Font-related error handling
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
        # Display-related errors
        elif "display" in str(e).lower():
            print("\nTip: This is a graphical interface error, but the chart should have been saved as an image file")
        sys.exit(1)

if __name__ == "__main__":
    main()
