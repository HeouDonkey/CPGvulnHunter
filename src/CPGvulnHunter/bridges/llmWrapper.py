from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
import time

from CPGvulnHunter.bridges.llmBridge import LLMBridge
from CPGvulnHunter.core.config import LLMConfig
from CPGvulnHunter.models.cpg.flowPath import FlowPath
from CPGvulnHunter.models.cpg.function import Function
from CPGvulnHunter.models.cpg.semantics import ParameterFlow, Semantic, Semantics
from CPGvulnHunter.models.llm.dataclass import LLMRequest
from CPGvulnHunter.models.llm.prompt import FunctionPrompt
from CPGvulnHunter.utils.llmCacher import LLMCacher





class LLMWrapper:
    """
    专门用于漏洞检测的LLM桥接类
    提供智能化的静态代码分析辅助功能
    """

    def __init__(self, llmConfig:LLMConfig):
        """
        初始化LLM桥接器
        
        :param llmConfig: LLM配置对象
        """
        self.logger = logging.getLogger(__name__)      
        self.logger.info("开始初始化LLM Wrapper...")
        
        # Ensure logger uses the level from config
        self.logger.setLevel(logging.getLogger().level)
        self.cacher = LLMCacher(llmConfig.cache_file)  # 初始化缓存器

        try:
            # 初始化LLM客户端
            self.logger.debug(f"LLM配置 - 模型: {llmConfig.model}, 基础URL: {llmConfig.base_url}")
            
            start_time = time.time()
            self.llm_client = LLMBridge(
                base_url=llmConfig.base_url,
                api_key=llmConfig.api_key,
                model=llmConfig.model
            )
            init_time = time.time() - start_time
            
            self.logger.info(f"LLM Wrapper初始化成功，耗时: {init_time:.2f}秒")
            self.logger.debug(f"LLM客户端类型: {type(self.llm_client).__name__}")
            
        except Exception as e:
            self.logger.error(f"LLM Wrapper初始化失败: {e}")
            import traceback
            self.logger.error(f"初始化错误堆栈: {traceback.format_exc()}")
            raise

        


    def analyze_external_functions(self, external_functions: List[Function]) -> Semantics:
        """
        分析外部函数并生成语义规则 - 逐个分析模式
        
        :param external_functions: 外部函数列表
        :return: 生成的语义规则对象
        """
        
        # 创建总的语义规则对象
        semantics = Semantics()
        
        if not external_functions:
            self.logger.warning("没有外部函数需要分析")
            return semantics
        
        start_time = time.time()
        self.logger.info(f"开始逐个分析 {len(external_functions)} 个外部函数")
        
        # 统计信息
        success_count = 0
        error_count = 0
        
        # 逐个分析每个函数
        for i, func in enumerate(external_functions, 1):
            func_start_time = time.time()
            try:
                func_name = getattr(func, 'full_name', f'function_{i}')
                self.logger.info(f"正在分析函数 {i}/{len(external_functions)}: {func_name}")
                
                # 分析单个函数
                semantic = self._analyze_single_external_function(func)
                
                if semantic is not None:
                    semantics.add_senmatic(semantic)
                    success_count += 1
                    func_time = time.time() - func_start_time
                    self.logger.info(f"函数 {func_name} 分析成功，耗时: {func_time:.2f}秒")
                else:
                    error_count += 1
                    self.logger.warning(f"函数 {func_name} 分析失败，跳过")
                    
            except Exception as e:
                error_count += 1
                func_name = getattr(func, 'full_name', f'function_{i}')
                self.logger.error(f"分析函数 {func_name} 时发生异常: {e}")
                continue
        
        total_time = time.time() - start_time
        self.logger.info(f"所有函数分析完成 - 成功: {success_count}, 失败: {error_count}, 总耗时: {total_time:.2f}秒")
        self.logger.info(f"总共生成 {len(semantics.semantic_list)} 条语义规则")
        
        if error_count > 0:
            self.logger.warning(f"有 {error_count} 个函数分析失败，成功率: {success_count/(success_count+error_count)*100:.1f}%")
        
        return semantics

    def _analyze_single_external_function(self, func: Function) -> Optional[Semantic]:
        """
        分析单个外部函数并生成语义规则
        
        :param func: 单个函数对象
        :return: 该函数的语义规则，失败时返回None
        """
        if not func or not isinstance(func, Function) or not hasattr(func, 'full_name'):
            self.logger.error("无效的函数对象，无法进行分析")
            return None
            
        func_name = func.full_name
        self.logger.debug(f"开始分析函数: {func_name}")
        cache = self.cacher.find_cache(func.generateSignature())
        if cache:
            self.logger.info(f"函数 {func_name} 的分析结果已在缓存中，直接返回")
            data = cache
        else:
            self.logger.info(f"函数 {func_name} 的分析结果不在缓存中，开始构建LLM请求")
            # 构建针对单个函数的提示词
            try:
                request = FunctionPrompt.build_semantic_analysis_request(func)
                self.logger.debug(f"为函数 {func_name} 构建分析请求完成")
            except Exception as e:
                self.logger.error(f"为函数 {func_name} 构建分析请求失败: {e}")
                return None
            
            # 发送请求并获取响应
            try:
                start_time = time.time()
                data: dict = self.llm_client.send(request, True)
                request_time = time.time() - start_time
                self.logger.debug(f"函数 {func_name} LLM请求完成，耗时: {request_time:.2f}秒")
                self.cacher.add_cache(func.generateSignature(), data)  # 缓存结果
            except Exception as e:
                self.logger.error(f"函数 {func_name} LLM请求失败: {e}")
                return None
        
        # Debug log: Print all data received from LLM
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"函数 {func_name} - LLM返回的完整数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 解析语义规则
        try:      
            # 安全地访问嵌套数据
            if not isinstance(data, dict):
                self.logger.error(f"函数 {func_name} - LLM返回数据不是字典类型: {type(data)}")
                return None
            
            # 处理嵌套结构：analysis_result.param_flows 或直接的 param_flows
            analysis_result = data.get('analysis_result', data)
            if not isinstance(analysis_result, dict):
                self.logger.error(f"函数 {func_name} - analysis_result 不是字典类型: {type(analysis_result)}")
                return None
            
            param_flows = []
            raw_param_flows = analysis_result.get('param_flows', [])
            self.logger.debug(f"函数 {func_name} 原始参数流数据: {raw_param_flows}")
            
            if isinstance(raw_param_flows, list):
                for flow_idx, flow in enumerate(raw_param_flows):
                    try:
                        if isinstance(flow, dict) and 'from' in flow and 'to' in flow:
                            # 创建 ParameterFlow 对象
                            param_flow = ParameterFlow(
                                from_param=flow['from'],
                                to_param=flow['to']
                            )
                            param_flows.append(param_flow)
                            self.logger.debug(f"函数 {func_name} 添加参数流 {flow_idx+1}: {flow['from']} -> {flow['to']}")
                        else:
                            self.logger.warning(f"函数 {func_name} 跳过无效的参数流格式: {flow}")
                    except Exception as flow_error:
                        self.logger.error(f"函数 {func_name} 处理参数流时出错: {flow_error}, 流数据: {flow}")
                        continue
            else:
                self.logger.warning(f"函数 {func_name} 参数流数据不是列表类型: {type(raw_param_flows)}")
            
            # 获取置信度信息
            confidence = analysis_result.get('confidence', 'unknown')
            reasoning = analysis_result.get('reasoning', '')
            
            # 创建并返回语义规则
            rule = Semantic(
                func_name,
                param_flows=param_flows,
                is_regex=False
            )
            
            self.logger.info(f"函数 {func_name} 语义规则生成成功 - 参数流数量: {len(param_flows)}, 置信度: {confidence}")
            if reasoning:
                self.logger.debug(f"函数 {func_name} 分析依据: {reasoning}")

            return rule
            
        except Exception as e:
            self.logger.error(f"解析函数 {func_name} 语义规则失败: {e}")
            self.logger.error(f"异常类型: {type(e).__name__}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            return None
    
    def analyze_dataflow(self,request:LLMRequest) -> Optional[dict]:
        """
        分析数据流路径并返回结果
        
        :param flowPath: 数据流路径对象
        """
        self.logger.debug("开始分析数据流路径")
        with open('./logs/llm_request.json', 'a', encoding='utf-8') as f:
            f.write(request.prompt + '\n')
        start_time = time.time()
        data: dict = self.llm_client.send(request, True)
        request_time = time.time() - start_time
        
        self.logger.debug(f"LLM请求完成，耗时: {request_time:.2f}秒")
        
        # 检查响应格式
        if not isinstance(data, dict):
            self.logger.error(f"LLM返回数据不是字典类型: {type(data)}")
            return None
        
        self.logger.debug(f"LLM响应数据包含 {len(data)} 个顶级字段: {list(data.keys())}")
        
        # 返回分析结果
        return data


    def function_clasification(self, llmRequest: LLMRequest) -> Optional[dict]:
        """
        分析单个函数的通用方法，只是做和大模型的交互，不进行任何分析。
        
        :param llmRequest: LLM请求对象
        :return: 分析结果字典或None
        """
        if not llmRequest:
            self.logger.error("LLM请求对象为空，无法进行分析")
            return None
        
        self.logger.debug(f"开始分析LLM请求")
        
        try:
            # 发送请求并获取响应
            start_time = time.time()
            data: dict = self.llm_client.send(llmRequest, True)
            request_time = time.time() - start_time
            self.logger.debug(f"LLM请求完成，耗时: {request_time:.2f}秒")
            
            # 检查响应格式
            if not isinstance(data, dict):
                self.logger.error(f"LLM返回数据不是字典类型: {type(data)}")
                return None
            
            self.logger.debug(f"LLM响应数据包含 {len(data)} 个顶级字段: {list(data.keys())}")
            
            # 返回分析结果
            return data
        
        except Exception as e:
            self.logger.error(f"分析函数时发生错误: {e}")
            self.logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            return None












