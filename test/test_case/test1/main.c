#include <stdio.h>
#include <string.h>




// 数据汇聚点（sink）- 可能的漏洞点
void dangerous_sink(char data[]) {
    printf("SINK: Received potentially dangerous data: %d\n", data);
    // 模拟危险操作，如系统调用、文件写入等
}

// 安全的数据汇聚点
void safe_sink(int data) {
    printf("SAFE SINK: Safely processed data: %d\n", data);
}

char* input() {
    char data[100];
    fgets(data,100,stdin);
    return data;
}

int main() {
    printf("=== 数据流传播测试 ===\n");
    char* ptr;
    char data[256];
    ptr = input();
    strncpy(data, ptr, sizeof(data) - 1);
    dangerous_sink(data);
    // memcpy(user_data, const void *, unsigned long) // This line is incomplete and should be removed or fixed

}
