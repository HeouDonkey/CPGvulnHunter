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
from CPGvulnHunter.utils.logger_config import LoggerConfigurator

class BasePass(ABC):
    """base pass class for all passes"""
    
    def __init__(self, cpg: CPG):
        self.name = "bassPass"
        self.cpg:CPG = cpg
        self.taget_area = "external"  # define the target area for this pass, can be 'external' or 'internal',which means all sink and source functions are external or internal functions
        self.taget_functions: List[Function] = []  # 存储分析目标的函数列表
        self.sources :list[Source] = []
        self.sinks: list[Sink] = []
        self.sanitizers: list[Function] = []  
        self.dataFlowResults: list[DataFlowResult] = []
        self.vulnerabilitiesResults: list[VulnerabilityResult] = []  # 存储漏洞分析结果
        self.logger = LoggerConfigurator.get_class_logger(self.__class__)
        # Ensure logger uses the level from config
        self.logger.setLevel(logging.getLogger().level)
        if self.taget_area == "external":
            self.taget_functions = self.cpg.external_functions
        elif self.taget_area == "internal":
            self.taget_functions = self.cpg.internal_functions

    def analysis_function(self) -> None:
        """
        分析每一个函数，将其分类为source、sink或sanitizer。
        这里使用LLM来分析函数的角色，并将结果存储在self.sources, self.sinks和self.sanitizers中。
        """
        functions = self.taget_functions
        for func in functions: 
            request = self.build_classify_method_request(func)
            response = self.cpg.llm_wrapper.function_clasification(request)
            if not response or 'analysis_result' not in response:
                logging.warning(f"LLM分析结果为空或格式不正确: {response}")
                return
            
            roles = response.get('analysis_result', {}).get('roles', [])
            for role in roles:
                role_type = role.get('role')
                parameter_index = role.get('parameter_index', -1)  # 默认-1表示返回值
                logging.info(f"函数 {func.name} 角色: {role_type}, 参数索引: {parameter_index}, 置信度: {role.get('confidence', 0.0)}, 理由: {role.get('reason', '')}")
                
                if role_type == 'SOURCE':
                    source = Source.create_from_function(func, index=parameter_index)
                    self.sources.append(source)
                elif role_type == 'SINK':
                    sink = Sink.create_from_function(func, index=parameter_index)
                    self.sinks.append(sink)
                elif role_type == 'SANITIZER':
                    self.sanitizers.append(func)

        self.logger.info(f"分析完成，找到 {len(self.sources)} 个源函数，{len(self.sinks)} 个汇聚点函数，{len(self.sanitizers)} 个清理函数")

    @abstractmethod
    def build_classify_method_request(self, func: Function) -> LLMRequest:
        pass

    def taint_analysis(self)  -> None:
        """执行污点分析"""
        if not self.cpg.joern_wrapper:
            logging.error("Joern wrapper未初始化，无法执行污点分析")
            return None
        semantics = self.cpg.external_semantics
        if not semantics or len(semantics.semantic_list) == 0:
            logging.error("没有可用的语义规则，五点分析可能存在问题！")
        for source in self.sources:
            for sink in self.sinks:
                try:
                    dataflow_result = self.cpg.joern_wrapper.run_taint_analysis(
                        source,
                        sink
                    )
                    if not dataflow_result:
                        logging.info(f"源 {source.full_name} 到汇聚点 {sink.full_name} 的数据流分析未找到路径")
                        continue
                    self.dataFlowResults.append(dataflow_result)
                    logging.info(f"分析源 {source.full_name} 到汇聚点 {sink.full_name} 的数据流结果: {dataflow_result}")   
                except Exception as e:
                    logging.error(f"分析源 {source.full_name} 到汇聚点 {sink.full_name} 时出错: {e}")
        return None

    def vuln_analysis(self):
        self.logger.info("开始执行漏洞数据流链条分析")
        if not self.cpg.joern_wrapper:
            self.logger.error("Joern wrapper未初始化，无法执行数据流分析")
            return None
        for result in self.dataFlowResults:
            for flow in result.flows:
                try:
                    self.logger.info(f"分析数据流路径: {flow}")
                    request = self.build_dataflow_analysis_request(flow)
                    self.logger.debug(f"构建的数据流分析请求: {request.prompt}")
                    result  = self.cpg.llm_wrapper.analyze_dataflow(request)
                    # 将结果转换为 DataflowResult 类型
                    if result and 'analysis_result' in result:
                        analysis = result['analysis_result']
                        analysis_result = VulnerabilityResult(
                            is_vulnerable=analysis.get('is_vulnerable', None),
                            confidence=analysis.get('confidence', None),
                            reason=analysis.get('reason', None),
                            flowPath_code=flow._get_function_chain()
                        )
                        self.vulnerabilitiesResults.append(analysis_result)
                        self.logger.info(f"数据流分析结果: {analysis_result}")
                    
                except Exception as e:
                    self.logger.error(f"分析数据流路径时出错: {e}")

    @abstractmethod
    def build_dataflow_analysis_request(self,path:FlowPath) -> LLMRequest:
        pass 

    def get_analysis_results(self) -> Dict[str, Any]:
        """获取分析结果，包含当前pass的所有信息"""
        sources_info = [source.to_dict() for source in self.sources]
        sinks_info = [sink.to_dict() for sink in self.sinks]
        sanitizers_info = [sanitizer.to_dict() for sanitizer in self.sanitizers]
        data_flow_results_info = [result.to_dict() for result in self.dataFlowResults]
        vulnerabilities_info = [vuln.to_dict() for vuln in self.vulnerabilitiesResults]
        result_info = {
            'sources': sources_info,
            'sinks': sinks_info,
            'sanitizers': sanitizers_info,
            'data_flow_results': data_flow_results_info,
            'analysis_results': vulnerabilities_info
        }
        self.logger.info(f"获取分析结果: {result_info}")
        return result_info
    
    
    def _save_results(self,output_path:str) -> None:
        """保存分析结果到指定路径"""
        try:
            analysis_results = self.get_analysis_results()
            # 修复路径操作：确保output_dir是Path对象
            output_dir = Path(output_path)
            
            # 生成时间戳文件夹（所有pass共享同一个时间戳文件夹）
            from datetime import datetime
            
            # 每个pass保存为单独的文件
            pass_name = self.name.lower().replace(" ", "_").replace("-", "_")
            save_path = output_dir / f"{pass_name}.json"
            
            with open(save_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(analysis_results, f, ensure_ascii=False, indent=4)
            self.logger.info(f"pass {self.name} 分析结果已保存到 {save_path}")
        except Exception as e:      
            self.logger.error(f"保存分析结果失败: {e}")
            raise RuntimeError(f"保存分析结果失败: {e}")
        
    def run(self,output_path: Optional[str] = None) -> None:
        """执行Pass分析"""
        logging.info(f"开始执行 {self.name} Pass")
        self.analysis_function()
        logging.info(f"找到 {len(self.sources)} 个源函数，{len(self.sinks)} 个汇聚点函数，{len(self.sanitizers)} 个清理函数")
        logging.info(f"源函数列表: {[source.full_name for source in self.sources]}")
        logging.info(f"汇聚点函数列表: {[sink.full_name for sink in self.sinks]}")
        logging.info(f"清理函数列表: {[sanitizer.full_name for sanitizer in self.sanitizers]}")
        # 对每个源-汇聚点对执行数据流分析
        self.taint_analysis()
        self.vuln_analysis()
        self._save_results(output_path)
        # 返回漏洞发现结果
        return None


