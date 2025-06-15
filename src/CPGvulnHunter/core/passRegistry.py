import importlib
from typing import Dict, Type, List, Optional
from pathlib import Path
from CPGvulnHunter.passes.basePass import BasePass
from CPGvulnHunter.utils.logger_config import LoggerConfigurator

class PassRegistry:
    """Pass注册表 - 静态类，用于管理所有可用的分析pass"""
    
    _registry: Dict[str, str] = {"init": "CPGvulnHunter.passes.initPass.InitPass","cwe78": "CPGvulnHunter.passes.cwe78.CWE78"}
    _loaded_classes: Dict[str, Type[BasePass]] = {}
    _logger = None  # 延迟初始化
    
    @classmethod
    def _get_logger(cls):
        """获取logger实例（延迟初始化）"""
        if cls._logger is None:
            cls._logger = LoggerConfigurator.get_class_logger(cls)
        return cls._logger
    
    @classmethod
    def register(cls, pass_name: str, pass_class_path: str) -> None:
        """
        注册一个pass
        
        Args:
            pass_name: pass名称（如 'init', 'cwe78'）
            pass_class_path: pass类的完整路径（如 'CPGvulnHunter.passes.initPass.InitPass'）
        """
        cls._registry[pass_name] = pass_class_path
        cls._get_logger().debug(f"注册Pass: {pass_name} -> {pass_class_path}")
    
    @classmethod
    def register_class(cls, pass_name: str, pass_class: Type[BasePass]) -> None:
        """
        直接注册一个pass类
        
        Args:
            pass_name: pass名称
            pass_class: pass类对象
        """
        cls._registry[pass_name] = f"{pass_class.__module__}.{pass_class.__name__}"
        cls._loaded_classes[pass_name] = pass_class
        cls._get_logger().debug(f"注册Pass类: {pass_name} -> {pass_class}")
    
    @classmethod
    def get_pass_class(cls, pass_name: str) -> Type[BasePass]:
        """
        获取pass类
        
        Args:
            pass_name: pass名称
            
        Returns:
            BasePass的子类
            
        Raises:
            ValueError: 如果pass未注册或加载失败
        """
        if pass_name not in cls._registry:
            raise ValueError(f"未注册的pass: {pass_name}. 可用的pass: {list(cls._registry.keys())}")
        
        # 如果已经加载过，直接返回
        if pass_name in cls._loaded_classes:
            return cls._loaded_classes[pass_name]
        
        # 动态加载类
        try:
            class_path = cls._registry[pass_name]
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            pass_class = getattr(module, class_name)
            
            # 验证是否是BasePass的子类
            if not issubclass(pass_class, BasePass):
                raise ValueError(f"Pass类 {class_path} 不是BasePass的子类")
            
            # 缓存加载的类
            cls._loaded_classes[pass_name] = pass_class
            cls._get_logger().debug(f"成功加载Pass类: {pass_name}")
            
            return pass_class
            
        except Exception as e:
            cls._get_logger().error(f"加载Pass类失败: {pass_name} - {e}")
            raise ValueError(f"无法加载pass: {pass_name} - {e}")
    
    @classmethod
    def get_available_passes(cls) -> List[str]:
        """获取所有已注册的pass名称"""
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, pass_name: str) -> bool:
        """检查pass是否已注册"""
        return pass_name in cls._registry
    
    @classmethod
    def auto_register_from_directory(cls, passes_dir: Optional[Path] = None) -> None:
        """
        自动从指定目录注册所有pass
        
        Args:
            passes_dir: passes目录路径，如果为None则使用默认路径
        """
        if passes_dir is None:
            # 使用默认的passes目录
            current_file = Path(__file__)
            passes_dir = current_file.parent.parent / "passes"
        
        if not passes_dir.exists():
            cls._get_logger().warning(f"Passes目录不存在: {passes_dir}")
            return
        
        cls._get_logger().info(f"开始自动注册Pass，扫描目录: {passes_dir}")
        
        # 扫描所有Python文件
        for py_file in passes_dir.glob("*.py"):
            if py_file.name.startswith("__") or py_file.name == "basePass.py":
                continue
            
            module_name = py_file.stem
            try:
                # 动态导入模块
                module = importlib.import_module(f'CPGvulnHunter.passes.{module_name}')
                
                # 在模块中查找BasePass的子类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePass) and 
                        attr != BasePass):
                        
                        # 使用模块名作为pass名称
                        pass_name = module_name.lower()
                        class_path = f"CPGvulnHunter.passes.{module_name}.{attr_name}"
                        
                        cls.register(pass_name, class_path)
                        cls._get_logger().info(f"自动注册Pass: {pass_name}")
                        break
                        
            except Exception as e:
                cls._get_logger().warning(f"无法自动注册模块 {module_name}: {e}")
    
    @classmethod
    def initialize_default_passes(cls) -> None:
        """初始化默认的pass注册表"""
        default_passes = {
            'init': 'CPGvulnHunter.passes.initPass.InitPass',
            'cwe78': 'CPGvulnHunter.passes.cwe78.CWE78',
            # 可以继续添加其他默认pass
        }
        
        for pass_name, class_path in default_passes.items():
            cls.register(pass_name, class_path)
        
        cls._get_logger().info(f"初始化默认Pass注册表: {list(default_passes.keys())}")
    
    @classmethod
    def clear_registry(cls) -> None:
        """清空注册表（主要用于测试）"""
        cls._registry.clear()
        cls._loaded_classes.clear()
        cls._get_logger().debug("清空Pass注册表")
    
    @classmethod
    def get_registry_info(cls) -> Dict[str, str]:
        """获取注册表信息"""
        return cls._registry.copy()