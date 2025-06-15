#!/bin/bash
# 设置工作目录为脚本所在目录
cd "$(dirname "$0")"


# 输入源代码目录
SOURCE_DIR="./C/testcases"  # 替换为你的源代码目录
# 输出预处理后的代码目录
OUTPUT_DIR="./output"  # 替换为你的输出目录
# 包含头文件的目录
INCLUDE_DIR="./C/testcasesupport"  # 替换为你的头文件目录

# 创建输出目录（如果不存在）
mkdir -p "$OUTPUT_DIR"

# 遍历源代码目录中的所有 .c 和 .cpp 文件
find "$SOURCE_DIR" -type f \( -name "*.c" -o -name "*.cpp" \) | while read -r file; do
    # 获取相对路径
    RELATIVE_PATH="${file#$SOURCE_DIR/}"
    # 创建对应的输出目录
    OUTPUT_FILE="$OUTPUT_DIR/$RELATIVE_PATH"
    mkdir -p "$(dirname "$OUTPUT_FILE")"

    # 预处理文件
    echo "Preprocessing $file -> $OUTPUT_FILE"
    gcc -E -P -I"$INCLUDE_DIR" "$file" -o "$OUTPUT_FILE"
done

echo "Preprocessing completed. Preprocessed files are in $OUTPUT_DIR."