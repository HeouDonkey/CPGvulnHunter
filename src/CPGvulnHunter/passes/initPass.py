from abc import ABC, abstractmethod
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from CPGvulnHunter.core.cpg import CPG
from CPGvulnHunter.models.cpg.function import Function
from CPGvulnHunter.passes.basePass import BasePass
from CPGvulnHunter.utils.logger_config import LoggerConfigurator


class InitPass():
    """
    初始化Pass - 负责外部函数语义分析和应用
    """

    def __init__(self, cpg: CPG) -> None:
        """
        :param cpg: CPG对象
        """
        self.logger = LoggerConfigurator.get_class_logger(self.__class__)
        self.cpg = cpg
        self.name = "initpass"  # 修改为小写，符合文件夹命名规范
        # InitPass不需要sources, sinks等，但需要记录语义分析结果
        self.semantic_rules_count = 0
        self.analyzed_functions_count = 0

    def apply_external_semantics(self):
        """
        Apply semantics to external functions
        """
        if not self.cpg.llm_wrapper:
            self.logger.error("LLM wrapper is not initialized.")
            return
        
        if not self.cpg.external_functions:
            self.logger.warning("No external functions to analyze.")
            return
            
        self.logger.info(f"开始分析 {len(self.cpg.external_functions)} 个外部函数...")
        self.analyzed_functions_count = len(self.cpg.external_functions)
        
        # analyze external functions nad generate semantics via llm
        self.cpg.external_semantics = self.cpg.llm_wrapper.analyze_external_functions(self.cpg.external_functions)
        if not self.cpg.external_semantics:
            self.logger.error("Failed to generate semantics for external functions.")
            return
            
        self.semantic_rules_count = len(self.cpg.external_semantics.semantic_list)
        self.logger.info(f"生成了 {self.semantic_rules_count} 条语义规则")
        
        # apply semantics to joern cpg
        if not self.cpg.joern_wrapper:
            self.logger.error("Joern wrapper is not initialized.")
            return
        self.cpg.joern_wrapper.apply_semantics(self.cpg.external_semantics)
        self.logger.info(f"Generated {len(self.cpg.external_semantics.semantic_list)} semantic rules for external functions.")

    def get_analysis_results(self) -> Dict[str, Any]:
        """获取InitPass的分析结果"""
        # 收集外部函数信息
        external_semantics_info = self.cpg.external_semantics.toString()
    
        result_info = {
            'pass_name': self.name,
            'analyzed_functions_count': self.analyzed_functions_count,
            'semantic_rules_count': self.semantic_rules_count,
            'semantic_rules': external_semantics_info,

        }
        
        self.logger.info(f"InitPass分析结果: 分析了{self.analyzed_functions_count}个函数，生成了{self.semantic_rules_count}条语义规则")
        return result_info

    def _save_results(self,output_path:str) -> None:
        """保存分析结果到指定路径"""
        try:
            analysis_results = self.get_analysis_results()

            
            # 生成时间戳文件夹（所有pass共享同一个时间戳文件夹）            
            
            with open(output_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(analysis_results, f, ensure_ascii=False, indent=4)
            self.logger.info(f"pass {self.name} 分析结果已保存到 {output_path}")
        except Exception as e:      
            self.logger.error(f"保存分析结果失败: {e}")
            raise RuntimeError(f"保存分析结果失败: {e}")

    def run(self,output_path: Optional[Path] = None) -> None:
        """执行InitPass分析"""
        self.logger.info(f"开始执行 {self.name}")
        # 应用外部函数语义分析
        self.apply_external_semantics()
        self._save_results(output_path)
        # 保存分析结果
        self.logger.info(f"{self.name} 执行完成")
        return None



