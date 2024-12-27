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

echo "Monitoring memory, CPU usage and GC of process: PID=$TARGET_PID"
echo "Log will be written to: $LOG_FILE"
echo "Press Ctrl+C to stop."

# 初始化累计值
TOTAL_MEM=0
TOTAL_CPU=0
TOTAL_YGC_COUNT=0
TOTAL_FGC_COUNT=0
TOTAL_YGC_TIME=0
TOTAL_FGC_TIME=0
YGC_EVENTS=0
FGC_EVENTS=0
COUNT=0

# 初始化上一次的GC计数和时间
LAST_YGC=0
LAST_FGC=0
LAST_YGCT=0
LAST_FGCT=0

# 函数：获取GC详细信息
get_gc_stats() {
  local pid=$1
  local gc_stats=$(jstat -gcutil $pid 2>/dev/null | tail -n 1)
  if [ -n "$gc_stats" ]; then
    echo "$gc_stats"
  else
    echo "0 0 0 0 0 0 0 0 0"
  fi
}

# 函数：安全的浮点数计算
calc() {
  echo "scale=3; $1" | bc
}

while true; do
  # 修改PS命令格式，确保输出为整数
  PROCESS_INFO=$(ps -p "$TARGET_PID" -o pid=,rss=,%cpu= --no-headers 2>/dev/null)

  if [ -n "$PROCESS_INFO" ]; then
    while read -r PID MEM_USAGE_KB CPU_USAGE; do
      # 获取GC统计信息
      GC_STATS=$(get_gc_stats $PID)

      # 解析GC统计信息
      read S0 S1 E O YGC YGCT FGC FGCT GCT <<<$(echo $GC_STATS)

      # 计算瞬时GC次数和时间
      if [ $COUNT -eq 0 ]; then
        INSTANT_YGC=0
        INSTANT_FGC=0
        INSTANT_YGCT=0
        INSTANT_FGCT=0
      else
        INSTANT_YGC=$(calc "$YGC - $LAST_YGC")
        INSTANT_FGC=$(calc "$FGC - $LAST_FGC")
        INSTANT_YGCT=$(calc "($YGCT - $LAST_YGCT) * 1000") # 转换为毫秒
        INSTANT_FGCT=$(calc "($FGCT - $LAST_FGCT) * 1000") # 转换为毫秒
      fi

      # 更新累计GC统计
      TOTAL_YGC_COUNT=$(calc "$TOTAL_YGC_COUNT + $INSTANT_YGC")
      TOTAL_FGC_COUNT=$(calc "$TOTAL_FGC_COUNT + $INSTANT_FGC")
      TOTAL_YGC_TIME=$(calc "$TOTAL_YGC_TIME + $INSTANT_YGCT")
      TOTAL_FGC_TIME=$(calc "$TOTAL_FGC_TIME + $INSTANT_FGCT")

      # 更新上一次的值
      LAST_YGC=$YGC
      LAST_FGC=$FGC
      LAST_YGCT=$YGCT
      LAST_FGCT=$FGCT

      # 将内存单位从 KB 转换为 MB
      MEM_USAGE_MB=$(calc "$MEM_USAGE_KB / 1024")

      # 更新累计值
      COUNT=$((COUNT + 1))
      TOTAL_MEM=$(calc "$TOTAL_MEM + $MEM_USAGE_MB")
      TOTAL_CPU=$(calc "$TOTAL_CPU + $CPU_USAGE")

      # 计算平均值
      AVG_MEM=$(calc "$TOTAL_MEM / $COUNT")
      AVG_CPU=$(calc "$TOTAL_CPU / $COUNT")

      # 计算有值的GC平均次数和时间
      if [ "$(calc "$INSTANT_YGC > 0")" = "1" ]; then
        YGC_EVENTS=$((YGC_EVENTS + 1))
      fi

      if [ "$(calc "$INSTANT_FGC > 0")" = "1" ]; then
        FGC_EVENTS=$((FGC_EVENTS + 1))
      fi

      if [ $YGC_EVENTS -gt 0 ]; then
        AVG_YGC_TIME=$(calc "$TOTAL_YGC_TIME / $YGC_EVENTS")
      else
        AVG_YGC_TIME=0
      fi

      if [ $FGC_EVENTS -gt 0 ]; then
        AVG_FGC_TIME=$(calc "$TOTAL_FGC_TIME / $FGC_EVENTS")
      else
        AVG_FGC_TIME=0
      fi

      # 计算平均 GC 次数
      if [ $COUNT -gt 0 ]; then
        if [ $YGC_EVENTS -gt 0 ]; then
          AVG_YGC_COUNT=$(calc "$TOTAL_YGC_COUNT / $YGC_EVENTS")
        else
          AVG_YGC_COUNT=0
        fi

        if [ $FGC_EVENTS -gt 0 ]; then
          AVG_FGC_COUNT=$(calc "$TOTAL_FGC_COUNT / $FGC_EVENTS")
        else
          AVG_FGC_COUNT=0
        fi
      else
        AVG_YGC_COUNT=0
        AVG_FGC_COUNT=0
      fi

      # 获取当前时间戳
      TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

      # 构建输出信息
      CURRENT_INFO="Current: $TIMESTAMP, PID=$PID, Memory=$MEM_USAGE_MB MB, CPU=$CPU_USAGE%"
      GC_INSTANT="Instant GC: Young GC=$INSTANT_YGC(${INSTANT_YGCT}ms), Full GC=$INSTANT_FGC(${INSTANT_FGCT}ms)"
      GC_AVG="Average GC: YGC=${AVG_YGC_COUNT}(${AVG_YGC_TIME}ms), FGC=${AVG_FGC_COUNT}(${AVG_FGC_TIME}ms)"
      AVERAGE_INFO="Average: Memory=$AVG_MEM MB, CPU=$AVG_CPU%"
      SEPARATOR="-------------------------------------------"

      # 输出到终端
      echo "$CURRENT_INFO"
      echo "$GC_INSTANT"
      echo "$GC_AVG"
      echo "$AVERAGE_INFO"
      echo "$SEPARATOR"

      # 写入日志
      echo "$CURRENT_INFO" >>"$LOG_FILE"
      echo "$GC_INSTANT" >>"$LOG_FILE"
      echo "$GC_AVG" >>"$LOG_FILE"
      echo "$AVERAGE_INFO" >>"$LOG_FILE"
      echo "$SEPARATOR" >>"$LOG_FILE"

    done <<<"$PROCESS_INFO"
  else
    echo "No process found with PID: $TARGET_PID"
    exit 1
  fi

  sleep "$INTERVAL"
done
