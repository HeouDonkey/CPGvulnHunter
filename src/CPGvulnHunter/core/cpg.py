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
from CPGvulnHunter.models.llm.llmConfig import LLMConfig
from CPGvulnHunter.core.config import UnifiedConfig


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
    
    # === 语义分析字段 ===
    external_semantics: Semantics = field(default_factory=Semantics)
    
    # === 元数据字段 ===
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 设置日志记录器
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.logger.info(f"开始初始化CPG - 源路径: {self.src_path}")
        
        # 验证源路径
        src_path_obj = Path(self.src_path)
        if not src_path_obj.exists():
            self.logger.error(f"源代码路径不存在: {self.src_path}")
            raise FileNotFoundError(f"源代码路径不存在: {self.src_path}")
        
        self.logger.debug(f"源路径验证通过: {self.src_path}")
        if src_path_obj.is_file():
            self.logger.info(f"检测到单个文件: {src_path_obj.name}")
        else:
            file_count = len(list(src_path_obj.rglob('*.[ch]')))  # 计算C文件数量
            self.logger.info(f"检测到目录，包含 {file_count} 个C源文件")
            
        # 如果没有提供配置，使用默认配置
        if self.config is None:
            self.logger.warning("未提供配置，使用默认配置")
            self.config = UnifiedConfig()
        else:
            self.logger.info(f"使用统一配置 - 项目: {self.config.project_name}, 版本: {self.config.version}")
            
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
            
        self.logger.info("CPG初始化完成")
    
    @classmethod
    def from_config_file(cls, src_path: str, config_file: str, **kwargs) -> 'CPG':
        """从配置文件创建 CPG 实例"""
        # 加载统一配置
        config = UnifiedConfig.from_file(config_file)
        
        # 应用kwargs覆盖
        if kwargs:
            # 可以在这里处理特定的kwargs覆盖逻辑
            logging.info(f"应用额外配置覆盖: {kwargs}")
        
        return cls(src_path=src_path, config=config, **kwargs)
    
    @classmethod 
    def from_config(cls, src_path: str, config: UnifiedConfig, **kwargs) -> 'CPG':
        """从统一配置对象创建 CPG 实例"""
        return cls(src_path=src_path, config=config, **kwargs)
    
    @property
    def cpg_var(self) -> str:
        """获取CPG变量名"""
        return self.config.joern.cpg_var if self.config else 'cpg'
    
    @property 
    def joern_path(self) -> str:
        """获取Joern路径"""
        return self.config.joern.installation_path if self.config else 'joern'
    
    @property
    def llm_config(self) -> LLMConfig:
        """获取LLM配置"""
        return self.config.llm if self.config else LLMConfig()
    
    @staticmethod
    def _load_config_file(config_path: Path) -> Dict[str, Any]:
        """加载配置文件（已弃用，使用UnifiedConfig.from_file）"""
        suffix = config_path.suffix.lower()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if suffix in ['.json']:
                return json.load(f)
            elif suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {suffix}")
    

    
