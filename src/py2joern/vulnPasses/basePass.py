from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from py2joern.cpgs.cpg import CPG
from py2joern.cpgs.models.flowPath import DataFlowResult
from py2joern.cpgs.models.sink import Sink
from py2joern.cpgs.models.source import Source
from py2joern.llmBridge.core.llmBridge import VulnerabilityLLMBridge

class VulnerabilityFinding:
    """漏洞发现结果"""
    
    def __init__(self, source: Source, sink: Sink, flow_path: DataFlowResult):
        self.source = source
        self.sink = sink
        self.flow_path = flow_path
    
    def to_dict(self) -> Dict[str, Any]:
        """将漏洞发现结果转换为字典"""
        return {
            "source": self.source.to_dict(),
            "sink": self.sink.to_dict(),
            "flow_path": self.flow_path.to_dict()
        }

class BaseAnalysisPass(ABC):
    """分析Pass基类"""
    
    def __init__(self, cpg:CPG,llmBridge:VulnerabilityLLMBridge):
        self.cpg:CPG = cpg
        self.llmBridge:VulnerabilityLLMBridge = llmBridge
        self.sources :list[Source] = []
        self.sinks: list[Sink] = []
        self.dataFlowResults: list[DataFlowResult] = []
        self.vulnerabilityFindings: List[VulnerabilityFinding] = []

    
