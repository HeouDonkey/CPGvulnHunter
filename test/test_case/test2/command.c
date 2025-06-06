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

// 汇聚点函数 - 直接命令执行
void execute_command(char* command) {
    printf("执行命令: %s\n", command);
    system(command);  
}

// 汇聚点函数 - 通过 popen 执行
void list_files(char* path) {
    char full_command[MAX_BUFFER];
    snprintf(full_command, sizeof(full_command), "ls %s", path);  // path 参数是 SINK
    
    FILE* pipe = popen(full_command, "r");
    if (pipe) {
        char output[256];
        while (fgets(output, sizeof(output), pipe)) {
            printf("文件: %s", output);
        }
        pclose(pipe);
    }
}

int main() {

    char* user_path = get_user_input();              // SOURCE
    char* validated_path = basic_validate(user_path); // SANITIZER
    list_files(validated_path);                      // SINK
    
    return 0;
}