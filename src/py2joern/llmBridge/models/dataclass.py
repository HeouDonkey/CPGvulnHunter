from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class AnalysisType(Enum):
    """分析类型枚举"""
    VULNERABILITY_DETECTION = "vulnerability_detection"
    SEMANTIC_RULES = "semantic_rules"
    SOURCE_SINK_IDENTIFICATION = "source_sink_identification"
    CODE_UNDERSTANDING = "code_understanding"
    FLOW_PATH_ANALYSIS = "flow_path_analysis"

@dataclass
class LLMRequest:
    """LLM请求数据结构"""
    analysis_type: AnalysisType
    system_content: str 
    prompt: str
    expected_format: str = "json"
    
    
    def to_messages(self) -> List[Dict[str, str]]:
        """转换为消息格式"""
        messages = [
            {"role": "system", "content": self.system_content},
            {"role": "user", "content": self.prompt}
        ]
        return messages
    
    def get_context_value(self, key: str, default=None):
        """获取上下文值"""
        return self.context.get(key, default)
    
    def set_context_value(self, key: str, value: Any):
        """设置上下文值"""
        self.context[key] = value

