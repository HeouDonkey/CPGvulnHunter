from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
from py2joern.cpgs.models.semantics import ParameterFlow
from py2joern.llmBridge.models.dataclass import LLMRequest
from py2joern.llmBridge.models.prompt import FunctionPrompt
from py2joern.cpgs.models.function import Function
from py2joern.cpgs.models.semantics import Semantic, Semantics
from py2joern.cpgs.models.flowPath import FlowPath, DataFlowResult
from py2joern.cpgs.models.source import Source
from py2joern.cpgs.models.sink import Sink

class AnalysisType(Enum):
    """分析类型枚举"""
    VULNERABILITY_DETECTION = "vulnerability_detection"
    SEMANTIC_RULES = "semantic_rules"
    SOURCE_SINK_IDENTIFICATION = "source_sink_identification"
    CODE_UNDERSTANDING = "code_understanding"
    FLOW_PATH_ANALYSIS = "flow_path_analysis"



class VulnerabilityLLMBridge:
    """
    专门用于漏洞检测的LLM桥接类
    提供智能化的静态代码分析辅助功能
    """

    def __init__(self, llm_client):
        """
        初始化LLM桥接器
        
        :param llm_client: 封装的llm_client
        :param config: 配置参数
        """
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)

        


    def analyze_external_functions(self, external_functions: List[Function]) -> Semantics:
        """
        分析外部函数并生成语义规则 - 逐个分析模式
        
        :param external_functions: 外部函数列表
        :return: 生成的语义规则对象
        """
        
        # 创建总的语义规则对象
        semantics = Semantics()
        self.logger.info(f"开始逐个分析 {len(external_functions)} 个外部函数")
        
        # 逐个分析每个函数
        for i, func in enumerate(external_functions, 1):
            try:
                self.logger.info(f"正在分析函数 {i}/{len(external_functions)}: {func.full_name}")
                # 分析单个函数
                semantic = self._analyze_single_external_function(func)
                semantics.add_senmatic(semantic)
            except Exception as e:
                self.logger.error(f"分析函数 {func.full_name} 时发生错误: {e}")
                continue
        self.logger.info(f"所有函数分析完成，总共生成 {len(semantics.semantic_list)} 条语义规则")
        return semantics

    def _analyze_single_external_function(self, func: Function) -> Semantic:
        """
        分析单个外部函数并生成语义规则
        
        :param func: 单个函数对象
        :return: 该函数的语义规则
        """
        # 构建针对单个函数的提示词
        request = FunctionPrompt.build_semantic_analysis_request(func)
        
        # 发送请求并获取响应
        data: dict = self.llm_client.send(request, True)
        
        # 解析语义规则
        try:      
            # 安全地访问嵌套数据
            if not isinstance(data, dict):
                self.logger.error(f"数据不是字典类型: {type(data)}")
                return None
            
            # 处理嵌套结构：analysis_result.param_flows 或直接的 param_flows
            analysis_result = data.get('analysis_result', data)
            if not isinstance(analysis_result, dict):
                self.logger.error(f"analysis_result 不是字典类型: {type(analysis_result)}")
                return None
            
            param_flows = []
            raw_param_flows = analysis_result.get('param_flows', [])
            
            if isinstance(raw_param_flows, list):
                for flow in raw_param_flows:
                    try:
                        if isinstance(flow, dict) and 'from' in flow and 'to' in flow:
                            # 创建 ParameterFlow 对象
                            param_flow = ParameterFlow(
                                from_param=flow['from'],
                                to_param=flow['to']
                            )
                            param_flows.append(param_flow)
                        else:
                            self.logger.warning(f"跳过无效的参数流格式: {flow}")
                    except Exception as flow_error:
                        self.logger.error(f"处理参数流时出错: {flow_error}, 流数据: {flow}")
                        continue
            
            # 创建并返回语义规则
            rule = Semantic(
                func.full_name,
                param_flows=param_flows,
                is_regex=False
            )
            
            self.logger.debug(f"为函数 {func.full_name} 添加语义规则，参数流数量: {len(param_flows)}")
            return rule
            
        except Exception as e:
            self.logger.error(f"解析函数 {func.full_name} 语义规则失败: {e}")
            self.logger.error(f"异常类型: {type(e).__name__}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            return None
    


    def analyze_function(self,llmRequest: LLMRequest) -> Optional[dict]:
        """
        分析函数并返回结果
        
        :param llmRequest: LLM请求对象
        :return: 分析结果字典或None
        """
        try:
            # 发送请求并获取响应
            data: dict = self.llm_client.send(llmRequest, True)
            
            # 检查响应格式
            if not isinstance(data, dict):
                self.logger.error(f"数据不是字典类型: {type(data)}")
                return None
            
            # 返回分析结果
            return data
        
        except Exception as e:
            self.logger.error(f"分析函数时发生错误: {e}")
            import traceback
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            return None

       

  








