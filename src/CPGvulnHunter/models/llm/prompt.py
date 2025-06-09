
from CPGvulnHunter.models.cpg.function import Function
from CPGvulnHunter.models.llm.dataclass import LLMRequest


class FunctionPrompt:
    """
    用于生成函数相关的提示内容
    """

    @staticmethod
    def build_semantic_analysis_request(func: Function) -> LLMRequest:
        """构建语义分析请求"""
        prompt = FunctionPrompt._build_semantic_analysis_prompt(func)
        return LLMRequest(
            system_content="你是一位资深的程序静态分析专家，专精于代码语义理解和数据流分析。你具备深厚的漏洞挖掘经验，能够准确识别函数间的数据流动模式，并为Joern静态分析框架生成精确的语义规则。\n\n**重要提示：请严格按照要求，只返回JSON格式的结果，不要包含任何解释文字、说明文档或代码块标记。**",
            prompt=prompt,
        )

    @staticmethod
    def _build_semantic_analysis_prompt(func: Function) -> str:
        """构建语义分析提示词"""
        function_info = f"函数名: {func.full_name}\n函数签名: {func.signature or '未知签名'}"
        function_useage = f"函数用法: {func.useage or '无描述'}"

        return f"""请为以下函数生成Joern静态分析框架所需的语义规则，重点分析参数间的数据流动关系。

## 目标函数信息
{function_info}
{function_useage}

## 分析任务
1. **数据流分析**: 识别函数参数之间的数据传递关系
2. **污点传播**: 确定哪些参数会将数据传递给其他参数或返回值
3. **语义规则生成**: 生成符合Joern框架的参数流映射规则

## 参数索引约定
- **-1**: 函数返回值
- **0**: 对象实例本身（this/self，适用于面向对象方法）
- **1, 2, 3...**: 函数参数按顺序编号（从1开始）

## 数据流分析原则
**重要：数据流表示的是污点数据的传播方向，即数据从哪里来到哪里去**

### 常见函数的数据流模式：
- **输入函数**（如 `fgets`, `scanf`, `read`）: 从数据源流向目标缓冲区
  - `fgets(buffer, size, stream)`: 数据从 stream(参数3) 流向 buffer(参数1) → `{{"from": 3, "to": 1}}`
- **复制函数**（如 `strcpy`, `memcpy`）: 从源流向目标
  - `strcpy(dest, src)`: 数据从 src(参数2) 流向 dest(参数1) → `{{"from": 2, "to": 1}}`
- **返回函数**（如 `malloc`, `strdup`）: 函数内部创建的数据流向返回值
  - `malloc(size)`: 分配的内存通过返回值返回 → `{{"from": 1, "to": -1}}`
- **格式化函数**（如 `sprintf`, `printf`）: 从格式化参数流向输出
  - `sprintf(buffer, format, ...)`: 格式化内容流向 buffer → `{{"from": 2, "to": 1}}`

## 数据流表示
- **from**: 源参数索引（数据来源）
- **to**: 目标参数索引（数据去向）
- 例如: `{{"from": 2, "to": 1}}` 表示第2个参数的数据流向第1个参数

## 特殊情况处理
- 如果函数不涉及数据传递，返回空的 param_flows 数组
- 如果函数有多个数据流路径，包含所有相关的流向
- 优先考虑安全关键的数据流（可能导致漏洞的流向）

## 严格要求
**请直接返回以下JSON格式的内容，不要添加任何解释文字、前言、后缀说明或代码块标记（如```json）：**

{{
    "analysis_result": {{
        "function_name": "{func.full_name}",
        "param_flows": [
            {{"from": 源参数索引, "to": 目标参数索引}},
            ...
        ],
        "confidence": "high|medium|low",
        "reasoning": "数据流分析依据说明"
    }}
}}

**再次强调：只返回上述JSON格式的内容，不要包含任何其他文字。**"""