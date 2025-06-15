#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_BUFFER 256

char* global_message = "Hello";   // 初始化的全局字符串指针



// 数据源函数 - 从用户输入获取数据
char* get_user_input() {
    static char input_buffer[MAX_BUFFER];
    printf("请输入文件名: ");
    fgets(input_buffer, sizeof(input_buffer), stdin);
    
    // 移除换行符
    size_t len = strlen(input_buffer);
    if (len > 0 && input_buffer[len-1] == '\n') {
        input_buffer[len-1] = '\0';
    }
    
    return input_buffer;  // 返回值是 SOURCE
}

char* basic_validate(char* input) {
    static char validated[MAX_BUFFER];
    strcpy(validated, input);
    
    char* dangerous[] = {"rm", "del"};
    int dangerous_count = sizeof(dangerous) / sizeof(dangerous[0]);
    
    for (int i = 0; i < dangerous_count; i++) {
        char* pos = strstr(validated, dangerous[i]);
        if (pos) {
            memset(pos, 'X', strlen(dangerous[i]));
        }
    }
    
    return validated;
}

// 添加消毒剂函数
char* sanitize_command(char* command) {
    static char sanitized[MAX_BUFFER];
    strcpy(sanitized, command);

    char* dangerous_keywords[] = {"rm", "del", ";", "&&", "||"};
    int dangerous_count = sizeof(dangerous_keywords) / sizeof(dangerous_keywords[0]);

    for (int i = 0; i < dangerous_count; i++) {
        char* pos = strstr(sanitized, dangerous_keywords[i]);
        if (pos) {
            memset(pos, 'X', strlen(dangerous_keywords[i]));
        }
    }

    return sanitized;
}

// 汇聚点函数 - 直接命令执行
void execute_command(char* command) {
    printf("原始命令: %s\n", command);

    // 使用消毒剂
    char* sanitized_command = sanitize_command(command);
    if (strcmp(command, sanitized_command) != 0) {
        printf("命令被消毒: %s\n", sanitized_command);
    }

    // 执行消毒后的命令
    printf("执行命令: %s\n", sanitized_command);
    system(sanitized_command);  
}

int main() {

    char* user_path = get_user_input();              // SOURCE
    execute_command(user_path);
    return 0;
}