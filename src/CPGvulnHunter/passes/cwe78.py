from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging
from pathlib import Path
from CPGvulnHunter.core.cpg import CPG
from CPGvulnHunter.bridges.llmWrapper import LLMWrapper
from CPGvulnHunter.models.cpg.function import Function
from CPGvulnHunter.models.cpg.source import Source
from CPGvulnHunter.models.cpg.sink import Sink
from CPGvulnHunter.models.cpg.flowPath import DataFlowResult, FlowPath
from CPGvulnHunter.models.llm.dataclass import LLMRequest
from CPGvulnHunter.models.llm.dataflowResult import VulnerabilityResult
from CPGvulnHunter.passes.basePass import BasePass
from CPGvulnHunter.utils.logger_config import LoggerConfigurator



class CWE78(BasePass):
    """CWE-78 OS命令注入分析Pass"""
    
    def __init__(self, cpg: CPG):
        super().__init__(cpg)
        self.name = "cwe78_command_injection"

    def build_classify_method_request(self, func: Function) -> LLMRequest:
        """获取函数分析的提示"""
        system_content = """你是一个专业的代码安全分析专家，专注于识别CWE-78（OS命令注入）漏洞。
    请分析给定的函数，判断其在命令注入攻击链中的角色，并精确定位具体的参数或返回值。

    角色定义：
    1. SOURCE: 可能引入不受信任数据的函数或参数
    - 用户输入函数（如scanf, fgets, getchar等）
    - 命令行参数（如argv）
    - 环境变量获取（如getenv）
    - 网络数据接收（如recv, read等）
    - 文件读取函数

    2. SINK: 可能执行OS命令的危险函数或参数
    - 直接命令执行（如system, exec系列函数）
    - 管道操作（如popen）
    - 脚本解释器调用

    3. SANITIZER: 可以清理/验证数据以防止命令注入的函数
    - 输入验证函数
    - 命令转义函数（如escapeshellarg）
    - 白名单过滤函数
    - 参数清理函数

    4. NONE: 与命令注入无关的函数

    **重要：必须精确定位source/sink的具体参数位置**
    - 参数索引：1表示第一个参数，2表示第二个参数，以此类推
    - 返回值：-1表示函数返回值
    - 对象实例：0表示this/self指针（面向对象方法）"""

        user_content = f"""请分析以下函数：

    {func.generateFunctionInfo()}

    请返回一个JSON对象，包含以下字段：
    {{
        "analysis_result": {{
            "function_name": "{func.full_name}",
            "roles": [
                {{
                    "role": "SOURCE|SINK|SANITIZER|NONE",
                    "parameter_index": "具体的参数索引（必填！）",
                    "confidence": "置信度（0.0-1.0）",
                    "reason": "判断理由，必须说明为什么这个具体参数是source/sink点",
                    "parameter_description": "参数描述（如'用户输入的命令字符串'、'待执行的系统命令'等）"
                }}
            ]
        }}
    }}

    **关键分析要求：**
    1. **精确定位参数**：不能只说函数是source/sink，必须明确指出哪个参数是source/sink点
    2. **参数索引准确性**：仔细分析函数签名，确保参数索引正确
    3. **多角色识别**：一个函数可能同时是source和sink（如某些参数是输入，某些参数是输出）
    4. **置信度要求**：只返回置信度 >= 0.6 的结果
    5. **详细说明**：在reason中明确说明为什么该参数是source/sink点

    **示例分析思路：**
    - `system(char* command)` → SINK, parameter_index: 1 (第一个参数command是执行点)
    - `fgets(char* str, int size, FILE* stream)` → SOURCE, parameter_index: 1 (第一个参数str接收用户输入)
    - `scanf("%s", buffer)` → SOURCE, parameter_index: 2 (第二个参数buffer接收用户输入)
    - `char* getenv(const char* name)` → SOURCE, parameter_index: -1 (返回值包含环境变量)
    - `execl(const char* path, const char* arg0, ...)` → SINK, parameter_index: 1 (第一个参数path是执行的命令路径)

    **特别注意：**
    - 对于variadic函数（如printf, execl），要考虑所有相关参数
    - 对于缓冲区操作函数，要区分输入缓冲区和输出缓冲区
    - 对于包装函数，要分析实际的数据流向"""

        return LLMRequest(system_content=system_content, prompt=user_content)

    def build_dataflow_analysis_request(self,path:FlowPath) -> LLMRequest:
        """构建数据流分析的提示"""
        system_content = """你是一个专业的代码安全分析专家，专注于识别CWE-78（OS命令注入）漏洞。
请分析以下数据流路径，判断其是否可能导致命令注入漏洞。

分析要求：
1. 重点关注数据流中的源（source）和汇聚点（sink）。
2. 如果数据流中存在清理函数（sanitizer），请判断该函数是否可以绕过。
3.从source点开始，跟踪漏洞的数据流，并一步步的进行分析。
3. 提供分析的置信度和理由。

请返回一个JSON对象，包含以下字段：
{
    "analysis_result": {
        "is_vulnerable": true|false,  # 是否存在漏洞
        "confidence": "置信度（0.0-1.0）",
        "reason": "判断理由",
        "sanitizers": ["清理函数列表"]
    }
}
"""

        user_content = f"""请分析以下数据流路径：

源（source）：{path.source.name}
汇聚点（sink）：{path.sink.name}

数据流路径：
{path.get_path_summary()}
"""

        return LLMRequest(system_content=system_content, prompt=user_content)







