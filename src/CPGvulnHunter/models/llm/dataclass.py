from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum



@dataclass
class LLMRequest:
    """LLM请求数据结构"""
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
    

