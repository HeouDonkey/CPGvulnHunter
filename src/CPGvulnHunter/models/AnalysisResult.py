
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    pass_name: str
    success: bool
    execution_time: float
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result_info :Dict[str, Any] = field(default_factory=dict)