"""
日志配置器模块

提供统一的日志配置功能，独立于数据类
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from CPGvulnHunter.core.config import LoggingConfig


class LoggerConfigurator:
    """日志配置器类 - 负责根据配置设置整个应用程序的日志系统"""
    
    @staticmethod
    def setup_logging(logging_config: LoggingConfig) -> None:
        """
        根据配置设置日志系统
        
        Args:
            logging_config: 日志配置对象
        """
        # 获取日志级别
        level = getattr(logging, logging_config.level.upper(), logging.INFO)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        formatter = logging.Formatter(logging_config.format)
        
        # 配置控制台处理器
        if logging_config.console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 配置文件处理器
        if logging_config.file:
            LoggerConfigurator._setup_file_handler(
                root_logger, 
                logging_config.file, 
                level, 
                formatter,
                logging_config.max_file_size,
                logging_config.backup_count
            )
    
    @staticmethod
    def _setup_file_handler(root_logger: logging.Logger, 
                           log_file: str,
                           level: int,
                           formatter: logging.Formatter,
                           max_file_size: str,
                           backup_count: int) -> None:
        """
        设置文件处理器
        
        Args:
            root_logger: 根日志记录器
            log_file: 日志文件路径
            level: 日志级别
            formatter: 格式化器
            max_file_size: 最大文件大小
            backup_count: 备份文件数量
        """
        try:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 解析文件大小
            size_bytes = LoggerConfigurator._parse_file_size(max_file_size)
            
            # 创建轮转文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=size_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # 如果文件处理器设置失败，至少保证控制台输出
            print(f"警告：文件日志处理器设置失败: {e}")
    
    @staticmethod
    def _parse_file_size(size_str: str) -> int:
        """
        解析文件大小字符串
        
        Args:
            size_str: 大小字符串，如 "10MB", "1GB"
            
        Returns:
            int: 字节数
        """
        size_str = size_str.upper().strip()
        
        # 提取数字和单位
        import re
        match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?B?)', size_str)
        if not match:
            return 10 * 1024 * 1024  # 默认10MB
        
        number, unit = match.groups()
        number = float(number)
        
        # 转换单位
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }
        
        if not unit:
            unit = 'B'
        elif unit == 'K':
            unit = 'KB'
        elif unit == 'M':
            unit = 'MB'
        elif unit == 'G':
            unit = 'GB'
        elif unit == 'T':
            unit = 'TB'
        
        return int(number * multipliers.get(unit, 1))
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        return logging.getLogger(name)
    
    @staticmethod
    def get_class_logger(cls) -> logging.Logger:
        """
        为类获取日志记录器
        
        Args:
            cls: 类对象
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        module_name = cls.__module__
        class_name = cls.__name__
        return logging.getLogger(f"{module_name}.{class_name}")
