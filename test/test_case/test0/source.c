#include <stdio.h>
#include <stdlib.h>

// 数据源函数 - 获取用户输入
int get_user_input() {
    printf("Enter a number: ");
    int value;
    scanf("%d", &value);
    return value;
}

// 同名函数 - 处理数据
int process_data(int data) {
    printf("source.c: processing data %d\n", data);
    return data * 2;
}

// 获取敏感数据源
char* get_sensitive_data() {
    return "sensitive_password_123";
}
