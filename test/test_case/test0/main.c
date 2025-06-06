#include <stdio.h>

// 声明外部函数
extern int get_user_input();
extern char* get_sensitive_data();
extern int transfer_data(int);
extern void handle_string(char*);
extern int validate_data(int);

// 数据汇聚点（sink）- 可能的漏洞点
void dangerous_sink(int data) {
    printf("SINK: Received potentially dangerous data: %d\n", data);
    // 模拟危险操作，如系统调用、文件写入等
}

// 安全的数据汇聚点
void safe_sink(int data) {
    printf("SAFE SINK: Safely processed data: %d\n", data);
}

int main() {
    printf("=== 数据流传播测试 ===\n");
    
    // 数据流1: 用户输入 -> 传输 -> 危险sink
    int user_data = get_user_input();
    int transferred = transfer_data(user_data);
    
    if (validate_data(transferred)) {
        safe_sink(transferred);
    } else {
        dangerous_sink(transferred);  // 潜在的安全问题
    }
    
    // 数据流2: 敏感数据 -> 字符串处理
    char* sensitive = get_sensitive_data();
    handle_string(sensitive);  // 敏感数据泄露
    
    printf("=== 测试完成 ===\n");
    return 0;
}
