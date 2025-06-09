from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import logging
import json
import yaml
from pathlib import Path

from CPGvulnHunter.models.llm.llmConfig import LLMConfig


@dataclass
class JoernConfig:
    """Joern配置"""
    installation_path: str = "joern"
    timeout: int = 300
    memory_limit: str = "8G"
    cpg_var: str = "cpg"
    workspace_path: str = "workspace"
    enable_cache: bool = True
    cache_dir: str = "cache"


@dataclass
class EngineConfig:
    """Engine核心配置"""
    max_call_depth: int = 20
    timeout_per_pass: int = 300  # 每个pass的超时时间（秒）
    parallel_execution: bool = False
    max_functions: int = 1000
    
    # 输出配置
    output_dir: str = "output"
    save_intermediate_results: bool = True
    report_format: str = "json"  # json, yaml, html
    
    # 分析配置
    enabled_passes: List[str] = field(default_factory=lambda: ["init"])
    pass_config: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pass_registry: Dict[str, str] = field(default_factory=dict)


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    console: bool = True
    max_file_size: str = "10MB"
    backup_count: int = 5


@dataclass
class VulnerabilityDetectionConfig:
    """漏洞检测配置"""
    timeout: int = 300
    confidence_threshold: float = 0.6
    max_paths: int = 100
    enable_path_optimization: bool = True
    cwe_types: List[str] = field(default_factory=lambda: ["CWE-78"])


@dataclass
class UnifiedConfig:
    """统一配置类 - 整合所有子系统的配置"""
    
    # 子配置模块
    llm: LLMConfig = field(default_factory=LLMConfig)
    joern: JoernConfig = field(default_factory=JoernConfig)
    engine: EngineConfig = field(default_factory=EngineConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    vulnerability_detection: VulnerabilityDetectionConfig = field(default_factory=VulnerabilityDetectionConfig)
    
    # 全局配置
    project_name: str = "CPGvulnHunter"
    version: str = "1.0.0"
    debug_mode: bool = False
    
    @classmethod
    def from_file(cls, config_file: str) -> 'UnifiedConfig':
        """从配置文件加载配置"""
        config_path = Path(config_file)
        
        logging.info(f"开始加载配置文件: {config_file}")
        
        if not config_path.exists():
            logging.warning(f"配置文件不存在: {config_file}，使用默认配置")
            return cls()
        
        # 读取配置文件
        try:
            config_data = cls._load_config_file(config_path)
            logging.info(f"配置文件读取成功，包含 {len(config_data)} 个顶级配置项")
            logging.debug(f"配置项: {list(config_data.keys())}")
        except Exception as e:
            logging.error(f"配置文件读取失败: {e}")
            raise
        
        # 创建各个子配置
        logging.debug("开始解析各子配置模块...")
        
        llm_config = LLMConfig()
        if 'llm' in config_data:
            llm_data = config_data['llm']
            llm_config = LLMConfig(**llm_data)
            logging.info(f"LLM配置加载成功 - 模型: {llm_config.model}, 基础URL: {llm_config.base_url}")
        elif 'llm_client' in config_data:  # 兼容旧格式
            logging.warning("检测到旧格式的llm_client配置，正在兼容处理...")
            llm_client_data = config_data['llm_client']
            llm_config = LLMConfig(
                api_key=llm_client_data.get('api_key', ''),
                base_url=llm_client_data.get('base_url', ''),
                model=llm_client_data.get('model', 'qwen2.5:14b')
            )
            logging.info(f"旧格式LLM配置转换成功 - 模型: {llm_config.model}")
        else:
            logging.warning("未找到LLM配置，使用默认值")
        
        joern_config = JoernConfig()
        if 'joern' in config_data:
            joern_data = config_data['joern']
            joern_config = JoernConfig(**joern_data)
            logging.info(f"Joern配置加载成功 - 安装路径: {joern_config.installation_path}")
            logging.debug(f"Joern配置详情: 超时={joern_config.timeout}s, 内存限制={joern_config.memory_limit}")
        else:
            logging.warning("未找到Joern配置，使用默认值")
        
        engine_config = EngineConfig()
        if 'engine' in config_data:
            engine_data = config_data['engine']
            engine_config = EngineConfig(
                max_call_depth=engine_data.get('max_call_depth', 20),
                timeout_per_pass=engine_data.get('timeout_per_pass', 300),
                parallel_execution=engine_data.get('parallel_execution', False),
                max_functions=engine_data.get('max_functions', 1000),
                output_dir=engine_data.get('output_dir', 'output'),
                save_intermediate_results=engine_data.get('save_intermediate_results', True),
                report_format=engine_data.get('report_format', 'json'),
                enabled_passes=engine_data.get('enabled_passes', ["init"]),
                pass_config=engine_data.get('pass_config', {}),
                pass_registry=engine_data.get('pass_registry', {})
            )
            logging.info(f"Engine配置加载成功 - 启用Pass: {engine_config.enabled_passes}")
            logging.debug(f"Engine配置详情: 最大调用深度={engine_config.max_call_depth}, 并行执行={engine_config.parallel_execution}")
        else:
            logging.warning("未找到Engine配置，使用默认值")
        
        logging_config = LoggingConfig()
        if 'logging' in config_data:
            logging_data = config_data['logging']
            logging_config = LoggingConfig(**logging_data)
            logging.info(f"日志配置加载成功 - 级别: {logging_config.level}")
        else:
            logging.warning("未找到日志配置，使用默认值")
        
        vuln_detection_config = VulnerabilityDetectionConfig()
        if 'vulnerability_detection' in config_data:
            vuln_data = config_data['vulnerability_detection']
            vuln_detection_config = VulnerabilityDetectionConfig(**vuln_data)
            logging.info(f"漏洞检测配置加载成功 - CWE类型: {vuln_detection_config.cwe_types}")
        else:
            logging.warning("未找到漏洞检测配置，使用默认值")
        
        # 提取全局配置
        global_config = {
            'project_name': config_data.get('project_name', 'CPGvulnHunter'),
            'version': config_data.get('version', '1.0.0'),
            'debug_mode': config_data.get('debug_mode', False)
        }
        
        return cls(
            llm=llm_config,
            joern=joern_config,
            engine=engine_config,
            logging=logging_config,
            vulnerability_detection=vuln_detection_config,
            **global_config
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'UnifiedConfig':
        """从字典创建配置"""
        return cls.from_file_data(config_dict)
    
    @classmethod
    def from_file_data(cls, config_data: Dict[str, Any]) -> 'UnifiedConfig':
        """从配置数据字典创建配置（内部方法）"""
        # 这个方法可以复用from_file中的逻辑
        instance = cls()
        
        # 更新各个子配置
        if 'llm' in config_data:
            instance.llm = LLMConfig(**config_data['llm'])
        if 'joern' in config_data:
            instance.joern = JoernConfig(**config_data['joern'])
        if 'engine' in config_data:
            instance.engine = EngineConfig(**config_data['engine'])
        if 'logging' in config_data:
            instance.logging = LoggingConfig(**config_data['logging'])
        if 'vulnerability_detection' in config_data:
            instance.vulnerability_detection = VulnerabilityDetectionConfig(**config_data['vulnerability_detection'])
            
        # 更新全局配置
        instance.project_name = config_data.get('project_name', instance.project_name)
        instance.version = config_data.get('version', instance.version)
        instance.debug_mode = config_data.get('debug_mode', instance.debug_mode)
        
        return instance
    
    @staticmethod
    def _load_config_file(config_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        suffix = config_path.suffix.lower()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if suffix in ['.json']:
                return json.load(f)
            elif suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {suffix}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'project_name': self.project_name,
            'version': self.version,
            'debug_mode': self.debug_mode,
            'llm': {
                'api_key': self.llm.api_key,
                'base_url': self.llm.base_url,
                'model': self.llm.model,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens,
                'timeout': self.llm.timeout
            },
            'joern': {
                'installation_path': self.joern.installation_path,
                'timeout': self.joern.timeout,
                'memory_limit': self.joern.memory_limit,
                'cpg_var': self.joern.cpg_var,
                'workspace_path': self.joern.workspace_path,
                'enable_cache': self.joern.enable_cache,
                'cache_dir': self.joern.cache_dir
            },
            'engine': {
                'max_call_depth': self.engine.max_call_depth,
                'timeout_per_pass': self.engine.timeout_per_pass,
                'parallel_execution': self.engine.parallel_execution,
                'max_functions': self.engine.max_functions,
                'output_dir': self.engine.output_dir,
                'save_intermediate_results': self.engine.save_intermediate_results,
                'report_format': self.engine.report_format,
                'enabled_passes': self.engine.enabled_passes,
                'pass_config': self.engine.pass_config
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file': self.logging.file,
                'console': self.logging.console,
                'max_file_size': self.logging.max_file_size,
                'backup_count': self.logging.backup_count
            },
            'vulnerability_detection': {
                'timeout': self.vulnerability_detection.timeout,
                'confidence_threshold': self.vulnerability_detection.confidence_threshold,
                'max_paths': self.vulnerability_detection.max_paths,
                'enable_path_optimization': self.vulnerability_detection.enable_path_optimization,
                'cwe_types': self.vulnerability_detection.cwe_types
            }
        }
    
    def save_to_file(self, config_file: str) -> None:
        """保存配置到文件"""
        config_path = Path(config_file)
        config_data = self.to_dict()
        
        suffix = config_path.suffix.lower()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if suffix in ['.json']:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            elif suffix in ['.yaml', '.yml']:
                yaml.safe_dump(config_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"不支持的配置文件格式: {suffix}")
    
    def setup_logging(self) -> None:
        """根据配置设置日志"""
        level = getattr(logging, self.logging.level.upper(), logging.INFO)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        formatter = logging.Formatter(self.logging.format)
        
        # 控制台处理器
        if self.logging.console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 文件处理器
        if self.logging.file:
            file_handler = logging.FileHandler(self.logging.file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    def validate(self) -> List[str]:
        """验证配置的有效性"""
        errors = []
        
        # 验证Joern路径
        joern_path = Path(self.joern.installation_path)
        if not joern_path.exists():
            errors.append(f"Joern安装路径不存在: {self.joern.installation_path}")
        
        # 验证LLM配置
        if not self.llm.api_key:
            errors.append("LLM API密钥未设置")
        if not self.llm.base_url:
            errors.append("LLM基础URL未设置")
        
        # 验证输出目录
        output_path = Path(self.engine.output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"无法创建输出目录 {self.engine.output_dir}: {e}")
        
        return errors
