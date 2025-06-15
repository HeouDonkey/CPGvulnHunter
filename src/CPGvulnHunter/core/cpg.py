from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging
import json
import yaml
import time
from pathlib import Path

from CPGvulnHunter.bridges.joernWrapper import JoernWrapper
from CPGvulnHunter.bridges.llmWrapper import LLMWrapper
from CPGvulnHunter.models.cpg.function import Function
from CPGvulnHunter.models.cpg.semantics import Semantics
from CPGvulnHunter.core.config import UnifiedConfig
from CPGvulnHunter.utils.logger_config import LoggerConfigurator


@dataclass
class CPG:
    """
    代码属性图（Code Property Graph）数据类
    
    纯数据容器，用于存储 CPG 相关的所有信息
    """
    
    # === 核心必需字段 ===
    src_path: str
    
    # === 统一配置 ===
    config: Optional[UnifiedConfig] = None
    
    # === wrapper ===
    llm_wrapper: Optional[LLMWrapper] = None
    joern_wrapper: Optional[JoernWrapper] = None

    # === 数据容器字段 ===
    functions: List[Function] = field(default_factory=list)
    external_functions: List[Function] = field(default_factory=list)
    internal_functions: List[Function] = field(default_factory=list)
    operator_functions: List[Function] = field(default_factory=list)
    function_fullName_list: List[str] = field(default_factory=list)
    functions_info :dict[str:list[str]] = field(default_factory=dict)  # 用于存储函数的详细信息，键为函数全名，值为函数对象
    # === 语义分析字段 ===
    external_semantics: Semantics = field(default_factory=Semantics)
    
    # === 元数据字段 ===
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    cpg_var: str = "cpg"  # 初始化 cpg_var 属性，默认值为 "cpg"
    


    
    def __post_init__(self):
        """初始化后处理"""
        # 设置日志记录器
        self.logger = LoggerConfigurator.get_class_logger(self.__class__)
        
        # Ensure logger uses the level from config
        self.logger.info(f"开始初始化CPG - 源路径: {self.src_path}")
        
        # 验证源路径
        src_path_obj = Path(self.src_path)
        if not src_path_obj.exists():
            self.logger.error(f"源代码路径不存在: {self.src_path}")
            raise FileNotFoundError(f"源代码路径不存在: {self.src_path}")
        
        # 初始化 Joern 包装器
        self.logger.info(f"初始化Joern包装器 - 安装路径: {self.config.joern.installation_path}")
        try:
            self.joern_wrapper = JoernWrapper(self.config.joern.installation_path)
            self.logger.info("Joern包装器初始化成功")
        except Exception as e:
            self.logger.error(f"Joern包装器初始化失败: {e}")
            raise
            
        # 初始化 LLM 包装器
        self.logger.info(f"初始化LLM包装器 - 模型: {self.config.llm.model}")
        try:
            self.llm_wrapper = LLMWrapper(self.config.llm)
            self.logger.info("LLM包装器初始化成功")
        except Exception as e:
            self.logger.error(f"LLM包装器初始化失败: {e}")
            raise
            
        # 导入代码到Joern
        self.logger.info("开始导入代码到Joern创建CPG...")
        try:
            import_start_time = time.time()
            self.joern_wrapper.import_code(self.src_path)
            import_duration = time.time() - import_start_time
            self.logger.info(f"代码导入完成，耗时: {import_duration:.2f}秒")
        except Exception as e:
            self.logger.error(f"代码导入失败: {e}")
            raise
        
        self.logger.info("开始获取所有函数...")
        try:
            self._get_all_functions()
            self.logger.info("所有函数获取成功")
        except Exception as e:
            self.logger.error(f"获取函数失败: {e}")
            raise
        self.logger.info("CPG初始化完成")
        self.logger.info(f"CPG实例创建成功 - 源路径: {self.src_path}, 函数总数: {len(self.functions)}")
        self.logger.debug(f"外部函数总数: {len(self.external_functions)}, 内部函数总数: {len(self.internal_functions)}, 操作符函数总数: {len(self.operator_functions)}")
        self.logger.debug(f"函数全名列表: {self.function_fullName_list}... (总计: {len(self.function_fullName_list)})")
        self.logger.debug(f"cpg_var 初始化为: {self.cpg_var}")
    
    @classmethod
    def from_config_file(cls, src_path: str, config: UnifiedConfig, **kwargs) -> 'CPG':
        """从配置文件创建 CPG 实例"""
        
        # 应用kwargs覆盖
        if kwargs:
            # 可以在这里处理特定的kwargs覆盖逻辑
            logging.info(f"应用额外配置覆盖: {kwargs}")
        
        return cls(src_path=src_path, config=config, **kwargs)

    def _get_all_functions(self) :
        joern_wrapper = self.joern_wrapper
        if not joern_wrapper:
            self.logger.error("Joern 包装器未初始化")
            return
        try:
            # 获取所有函数 fullName
            self.function_fullName_list = joern_wrapper.get_function_full_names(cpg_var=self.cpg_var)
            self.logger.info(f"发现函数全名总数: {len(self.function_fullName_list)}")
            # 获取所有函数对象
            for full_name in self.function_fullName_list:
                if not full_name:
                    self.logger.warning("函数全名为空，跳过")
                    continue
                function = self._get_single_function(full_name)
                if function and function.full_name:
                    if "<global>" in function.full_name:
                        self.operator_functions.append(function)
                    if function.is_external:
                        if function.full_name.startswith("<operator>"):
                            self.operator_functions.append(function)
                        else:
                            self.external_functions.append(function)
                            self.functions.append(function)
                    else:
                        self.internal_functions.append(function)
                        self.functions.append(function)
            self.logger.info(f"总函数数: {len(self.functions)}")
            self.logger.info(f"外部函数数: {len(self.external_functions)}")
            self.logger.info(f"内部函数数: {len(self.internal_functions)}")
            self.logger.info(f"操作符函数数: {len(self.operator_functions)}")
        except Exception as e:
            self.logger.error(f"获取所有函数失败: {e}")
            raise

    def _get_single_function(self,function_full_name: str) -> Optional[Function]:
        joern_wrapper = self.joern_wrapper
        if not joern_wrapper:
            self.logger.error("Joern wrapper is not initialized.")
            return None
        # 获取单个函数对象
        function = joern_wrapper.get_function_by_full_name(function_full_name, cpg_var=self.cpg_var)
        if not function:
            self.logger.error(f"Function {function_full_name} not found.")
            return None
        
        if function.full_name:
            if function.is_external:
                # fill parameter and useage for external functions,for joern cant generate signature for external functions
                if not function.full_name.startswith("<operator>"):
                    parameters = joern_wrapper.get_parameter(function, cpg_var=self.cpg_var)
                    function.set_parameters(parameters)
                    useage = joern_wrapper.find_useage(function)
                    function.set_useage(useage)                
            return function
        else:
            self.logger.warning(f"Function {function_full_name} not found.")
            return None




