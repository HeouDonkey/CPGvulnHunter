from asyncio import Task
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Type, Callable
import logging
from pathlib import Path
import json
import time
from datetime import datetime
import importlib

from CPGvulnHunter.core.cpg import CPG
from CPGvulnHunter.core.config import UnifiedConfig
from CPGvulnHunter.core.passRegistry import PassRegistry
from CPGvulnHunter.models.AnalysisResult import AnalysisResult
from CPGvulnHunter.passes.basePass import BasePass
from CPGvulnHunter.passes.initPass import InitPass
from CPGvulnHunter.passes.cwe78 import CWE78
from CPGvulnHunter.bridges.llmWrapper import LLMWrapper
from CPGvulnHunter.utils.logger_config import LoggerConfigurator
from CPGvulnHunter.core.task import Task

class VulnerabilityEngine:
    """
    CPG漏洞分析引擎
    
    核心职责：
    1. 管理CPG生命周期
    2. 协调分析passes执行
    3. 收集和处理分析结果
    4. 生成漏洞报告
    """
    
    def __init__(self, 
                 config_file: Optional[str] = None,
                 config: Optional[UnifiedConfig] = None):
        """
        初始化漏洞分析引擎
        
        Args:
            config_file: 配置文件路径
            config: 统一配置对象（与config_file二选一）
        """        
        # 加载配置
        if config is not None:
            self.config = config
        elif config_file is not None:
            self.config = UnifiedConfig.from_file(config_file)
        else:
            self.config = UnifiedConfig()
        
        # 使用LoggerConfigurator设置日志
        LoggerConfigurator.setup_logging(self.config.logging)
        self.logger = LoggerConfigurator.get_class_logger(self.__class__)
        self.logger.debug(f"配置文件: {config_file}")
        self.logger.debug(f"启用的分析passes: {self.config.engine.enabled_passes}")
        self.logger.debug(f"最大调用深度: {self.config.engine.max_call_depth}")
        self.logger.debug(f"并行执行: {self.config.engine.parallel_execution}")
        # 分析结果
        self.results: List[AnalysisResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        # 创建输出目录
        self.output_dir = Path(self.config.engine.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"输出目录: {self.output_dir.absolute()}")
        self.logger.info("引擎初始化完成")
    

    def run(self,src_path: str,passes:list[str]) :
        task = Task(target_src_path=src_path, output_path=self.output_dir, passes=passes,config = self.config)
        task.run()
        





if __name__ == "__main__":
    # 示例：快速分析
    
    src_path = "/home/nstl/data/CPGvulnHunter/test/test_case/test2"
    config_file = "/home/nstl/data/CPGvulnHunter/config.yml"
    engine = VulnerabilityEngine(config_file=config_file)
    engine.run(src_path=src_path, passes=['cwe78'])
