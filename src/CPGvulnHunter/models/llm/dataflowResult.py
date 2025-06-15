from dataclasses import dataclass
from typing import Optional, Dict, Any
import json


@dataclass
class VulnerabilityResult:
    """
    数据流分析结果数据类
    用于存储数据流分析的结果信息
    """
    is_vulnerable: bool = None
    confidence: float = None
    reason: str = None
    flowPath_code: str = None

    def to_dict(self):
        """
        将VulnerabilityResult对象转换为字典
        """
        return {
            "is_vulnerable": self.is_vulnerable,
            "confidence": self.confidence,
            "reason": self.reason,
            "flowPath_code": self.flowPath_code
        }

    def toJson(self, indent: Optional[int] = None) -> str:
        """
        将VulnerabilityResult对象转换为JSON字符串
        
        Args:
            indent: JSON缩进级别，None表示紧凑格式
            
        Returns:
            str: JSON格式的字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, default=str)

    @classmethod
    def fromJson(cls, json_str: str) -> 'VulnerabilityResult':
        """
        从JSON字符串创建VulnerabilityResult对象
        
        Args:
            json_str: JSON格式的字符串
            
        Returns:
            VulnerabilityResult: VulnerabilityResult对象实例
        """
        data = json.loads(json_str)
        return cls(**data)




