#include <stdio.h>
#include <string.h>

// 同名函数 - 处理数据（与source.c中的不同实现）
int process_data(int data) {
    printf("util.c: processing data %d\n", data);
    return data + 10;
}

// 数据传输函数
int transfer_data(int source_data) {
    int processed = process_data(source_data);
    return processed;
}

// 字符串处理函数
void handle_string(char* str) {
    printf("Handling string: %s\n", str);
    // 这里可能存在安全问题 - 直接打印敏感数据
}

// 数据验证函数
int validate_data(int data) {
    if (data > 100) {
        printf("Warning: data value %d is too large\n", data);
        return 0;
    }
    return 1;
}
