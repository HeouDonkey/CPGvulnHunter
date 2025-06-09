from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging

from CPGvulnHunter.core.cpg import CPG
from CPGvulnHunter.bridges.llmWrapper import LLMWrapper
from CPGvulnHunter.models.cpg.function import Function
from CPGvulnHunter.models.cpg.source import Source
from CPGvulnHunter.models.cpg.sink import Sink
from CPGvulnHunter.models.cpg.flowPath import DataFlowResult
from CPGvulnHunter.models.llm.dataclass import LLMRequest
from CPGvulnHunter.passes.basePass import BasePass



class CWE78(BasePass):
    """CWE-78 OS命令注入分析Pass"""
    
    def __init__(self, cpg: CPG):
        self.name = "CWE-78 OS Command Injection Analysis Pass"
        self.cpg:CPG = cpg
        self.sources :list[Source] = []
        self.sinks: list[Sink] = []
        self.sanitizers: list[Function] = []  
        self.dataFlowResults: list[DataFlowResult] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

    def analysis_function(self) -> None:
        """
        分析每一个函数，将其分类为source、sink或sanitizer。
        这里使用LLM来分析函数的角色，并将结果存储在self.sources, self.sinks和self.sanitizers中。
        """
        functions = self.cpg.functions
        for func in functions: 
            request = self.prompt(func)
            response = self.cpg.llm_wrapper.analyze_function(request)
            if response:  # 添加None检查
                self.reslove_response(response, func)
        self.logger.info(f"分析完成，找到 {len(self.sources)} 个源函数，{len(self.sinks)} 个汇聚点函数，{len(self.sanitizers)} 个清理函数")



    def reslove_response(self, response: dict, func: Function) -> None:
        """解析LLM的响应，提取源、汇聚点和清理函数"""
        if not response or 'analysis_result' not in response:
            logging.warning(f"LLM分析结果为空或格式不正确: {response}")
            return
        
        roles = response.get('analysis_result', {}).get('roles', [])
        for role in roles:
            role_type = role.get('role')
            if role_type == 'NONE':
                # 与命令注入无关的函数
                continue
                
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

    def prompt(self, func: Function) -> LLMRequest:
        """获取函数分析的提示"""
        system_content = """你是一个专业的代码安全分析专家，专注于识别CWE-78（OS命令注入）漏洞。
    请分析给定的函数，判断其在命令注入攻击链中的角色。

    角色定义：
    1. SOURCE: 可能引入不受信任数据的函数
    - 用户输入函数（如scanf, fgets, getchar等）
    - 命令行参数（如argv）
    - 环境变量获取（如getenv）
    - 网络数据接收（如recv, read等）
    - 文件读取函数

    2. SINK: 可能执行OS命令的危险函数
    - 直接命令执行（如system, exec系列函数）
    - 管道操作（如popen）
    - 脚本解释器调用

    3. SANITIZER: 可以清理/验证数据以防止命令注入的函数
    - 输入验证函数
    - 命令转义函数（如escapeshellarg）
    - 白名单过滤函数
    - 参数清理函数

    4. NONE: 与命令注入无关的函数"""

        user_content = f"""请分析以下函数：

    {func.generateFunctionInfo()}

    请返回一个JSON对象，包含以下字段：
    {{
        "analysis_result": {{
            "function_name": "{func.full_name}",
            "roles": [
                {{
                    "role": "SOURCE|SINK|SANITIZER|NONE",
                    "parameter_index": "参数索引（-1表示返回值，1表示第一个参数等）",
                    "confidence": "置信度（0.0-1.0）",
                    "reason": "判断理由",
                }}
            ]
        }}
    }}

    分析要求：
    1. 一个函数可能具有多个角色
    2. 只返回置信度 >= 0.6 的结果
    3. 重点关注函数的实际行为，不仅仅是函数名
    4. 考虑函数参数的用途和返回值的性质

    示例分析思路：
    - 如果函数从用户获取输入 → 可能是SOURCE
    - 如果函数执行系统命令 → 可能是SINK  
    - 如果函数验证或清理输入 → 可能是SANITIZER
    - 如果函数与命令执行无关 → 标记为NONE"""

        return LLMRequest(system_content=system_content, prompt=user_content)


    def taint_analysis(self)  -> None:
        """执行污点分析"""
        if not self.cpg.joern_wrapper:
            logging.error("Joern wrapper未初始化，无法执行污点分析")
            return None
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

    def get_analysis_results(self) -> Dict[str, Any]:
        """获取分析结果，包含当前pass的所有信息"""
        sources_info = [source.to_dict() for source in self.sources]
        sinks_info = [sink.to_dict() for sink in self.sinks]
        sanitizers_info = [sanitizer.to_dict() for sanitizer in self.sanitizers]
        data_flow_results_info = [result.to_dict() for result in self.dataFlowResults]
        return {
            "name": self.name,
            "sources": sources_info,
            "sinks": sinks_info,
            "sanitizers": sanitizers_info,
            "data_flow_results": data_flow_results_info
        }
        

    def run(self):
        """执行Pass分析"""
        logging.info(f"开始执行 {self.name} Pass")
        self.analysis_function()
        logging.info(f"找到 {len(self.sources)} 个源函数，{len(self.sinks)} 个汇聚点函数，{len(self.sanitizers)} 个清理函数")
        logging.info(f"源函数列表: {[source.full_name for source in self.sources]}")
        logging.info(f"汇聚点函数列表: {[sink.full_name for sink in self.sinks]}")
        logging.info(f"清理函数列表: {[sanitizer.full_name for sanitizer in self.sanitizers]}")
        # 对每个源-汇聚点对执行数据流分析
        self.taint_analysis()
        self.optimize_paths()
        
        # 返回漏洞发现结果
        return None
    
    def optimize_paths(self) -> None:
        """优化路径分析（需要实现）"""
        # TODO: 实现路径优化逻辑
        pass


