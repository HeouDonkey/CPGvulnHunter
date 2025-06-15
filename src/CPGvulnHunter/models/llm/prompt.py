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
        function_info = f"函数名: {func.full_name}\n函数签名: {func.get_sigenature() or '未知签名'}\n"
        function_useage = f"函数用法: {func.useage or '无描述'}"

        return f"""请为以下函数生成Joern静态分析框架所需的语义规则，重点分析参数间的数据流动关系。

## 目标函数信息
{function_info}
{function_useage}

## 分析任务
1. **数据流分析**: 识别函数参数之间的数据传递关系
2. **污点传播**: 确定哪些参数会将数据传递给其他参数或返回值
3. **参数透传**: 确保污点在函数调用过程中不会断掉
4. **语义规则生成**: 生成符合Joern框架的参数流映射规则

## 参数索引约定
- **-1**: 函数返回值
- **0**: 对象实例本身（this/self，适用于面向对象方法）
- **1, 2, 3...**: 函数参数按顺序编号（从1开始）

## 数据流分析原则
**重要：数据流表示的是污点数据的传播方向，包括参数间传递、参数透传和参数到返回值的传递**

### 数据流类型说明：

#### 1. 参数透传 (Parameter Pass-Through) - **必须包含**
**关键：为了确保污点分析的连续性，每个可能被污染的参数都必须包含自传递映射**
- 所有可能携带污点的参数都需要透传给自身，防止污点链断裂
- `{{"from": 1, "to": 1}}` - 参数1透传给自身
- `{{"from": 2, "to": 2}}` - 参数2透传给自身
- `{{"from": 3, "to": 3}}` - 参数3透传给自身

**示例**：`strcpy(dest, src)`
- 必须包含：`{{"from": 1, "to": 1}}` (dest透传) 和 `{{"from": 2, "to": 2}}` (src透传)

#### 2. 参数间传递 (Parameter-to-Parameter Flow)
- **输入函数**（如 `fgets`, `scanf`, `read`）: 从数据源流向目标缓冲区
  - `fgets(buffer, size, stream)`: 数据从 stream(参数3) 流向 buffer(参数1)
  - 流向: `{{"from": 3, "to": 1}}`
  - **必须添加透传**: `{{"from": 1, "to": 1}}, {{"from": 2, "to": 2}}, {{"from": 3, "to": 3}}`

- **复制函数**（如 `strcpy`, `memcpy`）: 从源流向目标  
  - `strcpy(dest, src)`: 数据从 src(参数2) 流向 dest(参数1)
  - 流向: `{{"from": 2, "to": 1}}`
  - **必须添加透传**: `{{"from": 1, "to": 1}}, {{"from": 2, "to": 2}}`

#### 3. 参数到返回值传递 (Parameter-to-Return Flow)
- **查询/计算函数**（如 `strlen`, `strcmp`, `strstr`）: 参数内容影响返回值
  - `strlen(str)`: 参数1的内容决定返回值
  - 流向: `{{"from": 1, "to": -1}}`
  - **必须添加透传**: `{{"from": 1, "to": 1}}`
  
- **分配函数**（如 `malloc`, `calloc`）: 参数决定分配大小，返回分配的内存
  - `malloc(size)`: 参数1影响返回的内存
  - 流向: `{{"from": 1, "to": -1}}`
  - **必须添加透传**: `{{"from": 1, "to": 1}}`

#### 4. 完整的数据流映射 (Complete Flow Mapping)
对于复杂函数，需要包含所有相关的数据流：

- **格式化函数** `sprintf(buffer, format, arg1, arg2, ...)`:
  - 参数透传: `{{"from": 1, "to": 1}}, {{"from": 2, "to": 2}}, {{"from": 3, "to": 3}}, {{"from": 4, "to": 4}}`
  - 格式字符串到缓冲区: `{{"from": 2, "to": 1}}`
  - 参数到缓冲区: `{{"from": 3, "to": 1}}, {{"from": 4, "to": 1}}`
  - 参数到返回值: `{{"from": 2, "to": -1}}, {{"from": 3, "to": -1}}, {{"from": 4, "to": -1}}`

- **搜索函数** `strstr(haystack, needle)`:
  - 参数透传: `{{"from": 1, "to": 1}}, {{"from": 2, "to": 2}}`
  - 两个参数都影响返回值: `{{"from": 1, "to": -1}}, {{"from": 2, "to": -1}}`

- **比较函数** `strcmp(str1, str2)`:
  - 参数透传: `{{"from": 1, "to": 1}}, {{"from": 2, "to": 2}}`
  - 两个参数都影响返回值: `{{"from": 1, "to": -1}}, {{"from": 2, "to": -1}}`

## 数据流表示规范
- **from**: 源参数索引（数据来源）
- **to**: 目标参数索引（数据去向）
- **必须包含所有相关的数据流路径，特别是参数透传映射**

### 参数透传规则（关键！）：
1. **所有输入参数都必须包含自传递映射** (1→1, 2→2, 3→3, ...)
2. **输出参数（被修改的参数）也必须包含自传递映射**
3. **即使参数只是用于控制逻辑，也可能需要透传以保持污点连续性**

### 常见数据流模式总结：
1. **输入类**: `参数透传` + `外部源 → 缓冲区` + `外部源 → 返回值`
2. **复制类**: `参数透传` + `源参数 → 目标参数` + `源参数 → 返回值`
3. **查询类**: `参数透传` + `所有输入参数 → 返回值`
4. **修改类**: `参数透传` + `输入参数 → 返回值`

## 特殊情况处理
- 如果函数不涉及数据传递，仍需考虑参数透传映射
- 如果函数有多个数据流路径，**必须包含所有相关的流向和透传**
- 优先考虑安全关键的数据流（可能导致漏洞的流向）
- **绝对不能遗漏参数透传映射，这会导致污点分析断链**

## 严格要求
**请直接返回以下JSON格式的内容，不要添加任何解释文字、前言、后缀说明或代码块标记（如```json）：**

{{
    "analysis_result": {{
        "function_name": "{func.full_name}",
        "param_flows": [
            {{"from": 源参数索引, "to": 目标参数索引}},
            {{"from": 源参数索引, "to": -1}},
            ...
        ],
        "confidence": "high|medium|low",
        "reasoning": "数据流分析依据说明，包括参数间传递、参数透传和参数到返回值传递的详细分析"
    }}
}}

## 示例分析

### 示例1: `strcpy(dest, src)`
```
param_flows: [
    {{"from": 1, "to": 1}},  // dest透传（必须）
    {{"from": 2, "to": 2}},  // src透传（必须）
    {{"from": 2, "to": 1}},  // src → dest
    {{"from": 2, "to": -1}}  // src → 返回值
]
```

### 示例2: `strlen(str)`
```
param_flows: [
    {{"from": 1, "to": 1}},  // str透传（必须）
    {{"from": 1, "to": -1}}  // str → 返回值
]
```

### 示例3: `sprintf(buffer, format, arg1, arg2)`
```
param_flows: [
    {{"from": 1, "to": 1}},   // buffer透传（必须）
    {{"from": 2, "to": 2}},   // format透传（必须）
    {{"from": 3, "to": 3}},   // arg1透传（必须）
    {{"from": 4, "to": 4}},   // arg2透传（必须）
    {{"from": 2, "to": 1}},   // format → buffer
    {{"from": 3, "to": 1}},   // arg1 → buffer  
    {{"from": 4, "to": 1}},   // arg2 → buffer
    {{"from": 2, "to": -1}},  // format → 返回值
    {{"from": 3, "to": -1}},  // arg1 → 返回值
    {{"from": 4, "to": -1}}   // arg2 → 返回值
]
```

### 示例4: `strcmp(str1, str2)`
```
param_flows: [
    {{"from": 1, "to": 1}},  // str1透传（必须）
    {{"from": 2, "to": 2}},  // str2透传（必须）
    {{"from": 1, "to": -1}}, // str1 → 返回值
    {{"from": 2, "to": -1}}  // str2 → 返回值
]
```

**再次强调：必须包含所有参数的透传映射（N→N），这是保证污点分析连续性的关键！同时包含所有相关的数据流路径。**"""