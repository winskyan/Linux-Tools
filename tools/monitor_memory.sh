#!/bin/bash

# 目标 PID
TARGET_PID=$1
# 检查间隔（秒）
INTERVAL=5
# 输出日志文件
LOG_FILE="usage.log"

if [ -z "$TARGET_PID" ]; then
  echo "Usage: $0 <pid>"
  exit 1
fi

echo "Monitoring memory and CPU usage of process: PID=$TARGET_PID"
echo "Log will be written to: $LOG_FILE"
echo "Press Ctrl+C to stop."

# 初始化累计值
TOTAL_MEM=0
TOTAL_CPU=0
COUNT=0

while true; do
  # 获取进程内存和 CPU 信息
  PROCESS_INFO=$(ps -p "$TARGET_PID" -o pid,rss,%cpu --no-headers)

  if [ -n "$PROCESS_INFO" ]; then
    while read -r PID MEM_USAGE_KB CPU_USAGE; do
      # 将内存单位从 KB 转换为 MB，保留两位小数
      MEM_USAGE_MB=$(awk "BEGIN {printf \"%.2f\", $MEM_USAGE_KB / 1024}")

      # 更新累计值
      COUNT=$((COUNT + 1))
      TOTAL_MEM=$(awk "BEGIN {printf \"%.2f\", $TOTAL_MEM + $MEM_USAGE_MB}")
      TOTAL_CPU=$(awk "BEGIN {printf \"%.2f\", $TOTAL_CPU + $CPU_USAGE}")

      # 计算平均值
      AVG_MEM=$(awk "BEGIN {printf \"%.2f\", $TOTAL_MEM / $COUNT}")
      AVG_CPU=$(awk "BEGIN {printf \"%.2f\", $TOTAL_CPU / $COUNT}")

      # 获取当前时间戳
      TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

      # 构建输出信息
      CURRENT_INFO="Current: $TIMESTAMP, PID=$PID, Memory=$MEM_USAGE_MB MB, CPU=$CPU_USAGE%"
      AVERAGE_INFO="Average: Memory=$AVG_MEM MB, CPU=$AVG_CPU%"
      SEPARATOR="-------------------------------------------"

      # 输出到终端
      echo "$CURRENT_INFO"
      echo "$AVERAGE_INFO"
      echo "$SEPARATOR"

      # 写入日志
      echo "$CURRENT_INFO" >>"$LOG_FILE"
      echo "$AVERAGE_INFO" >>"$LOG_FILE"
      echo "$SEPARATOR" >>"$LOG_FILE"

      # 同时保留原始数据格式的记录
      # echo "$TIMESTAMP,$PID,$MEM_USAGE_MB,$CPU_USAGE,$AVG_MEM,$AVG_CPU" >>"$LOG_FILE"
      # echo "" >>"$LOG_FILE" # 添加空行以增加可读性
    done <<<"$PROCESS_INFO"
  else
    echo "No process found with PID: $TARGET_PID"
    exit 1
  fi

  sleep "$INTERVAL"
done
