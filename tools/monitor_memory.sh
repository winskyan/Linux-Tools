#!/bin/bash

# 目标 PID
TARGET_PID=$1
# 检查间隔（秒）
INTERVAL=5
# 输出日志文件
LOG_FILE="memory_usage.log"

if [ -z "$TARGET_PID" ]; then
  echo "Usage: $0 <pid>"
  exit 1
fi

echo "Monitoring memory usage of process: PID=$TARGET_PID"
echo "Log will be written to: $LOG_FILE"
echo "Press Ctrl+C to stop."

# 写入日志头
echo "Timestamp,PID,Memory_Usage(MB)" > "$LOG_FILE"

while true; do
  # 获取进程内存信息
  PROCESS_INFO=$(ps -p "$TARGET_PID" -o pid,rss --no-headers)
  
  if [ -n "$PROCESS_INFO" ]; then
    while read -r PID MEM_USAGE_KB; do
      # 将内存单位从 KB 转换为 MB，保留两位小数
      MEM_USAGE_MB=$(awk "BEGIN {printf \"%.2f\", $MEM_USAGE_KB / 1024}")
      
      # 获取当前时间戳
      TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
      
      # 输出到终端
      echo "$TIMESTAMP, $PID, $MEM_USAGE_MB MB"
      
      # 写入日志
      echo "$TIMESTAMP, $PID, $MEM_USAGE_MB" >> "$LOG_FILE"
    done <<< "$PROCESS_INFO"
  else
    echo "No process found with PID: $TARGET_PID"
  fi
  
  sleep "$INTERVAL"
done
