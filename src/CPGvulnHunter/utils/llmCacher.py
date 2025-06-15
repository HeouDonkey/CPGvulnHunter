import json
import atexit
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

class LLMCacher:
    """
    A class to cache LLM responses to avoid redundant API calls.
    """

    def __init__(self, cache_file: str = "llm_cache.json"):
        self.cache_file = cache_file
        self.logger = logging.getLogger(__name__)

        self.caches = self._load_cache()
        self._dirty = False  # 标记缓存是否被修改
        
        # 注册退出时保存缓存
        atexit.register(self._safe_save_cache)

    def __enter__(self):
        """进入上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器时保存缓存"""
        self.save_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """加载缓存文件"""
        if self.cache_file:
            try:
                with open(self.cache_file, 'r+', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                self.logger.debug(f"无法加载缓存文件 {self.cache_file}: {e}")
                return {}
        return {}

    def find_cache(self, request) -> Optional[Any]:
        """查找缓存的响应"""
        if not self.caches:
            return None
        key = self._calculate_cache_key(request)
        return self.caches.get(key)
    
    def add_cache(self, request, response):
        """添加新的缓存条目"""
        key = self._calculate_cache_key(request)
        self.caches[key] = response
        self._dirty = True  # 标记缓存已修改

    def _calculate_cache_key(self, request) -> str:
        """计算请求的唯一缓存键"""
        import hashlib
        if hasattr(request, '__dict__'):
            request_str = str(sorted(request.__dict__.items()))
        else:
            request_str = str(request)
        
        return hashlib.md5(request_str.encode('utf-8')).hexdigest()

    def save_cache(self):
        """保存缓存到文件"""
        if self.cache_file and self.caches and self._dirty:
            try:
                # 确保目录存在
                import os
                os.makedirs(os.path.dirname(self.cache_file) if os.path.dirname(self.cache_file) else '.', exist_ok=True)
                
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.caches, f, indent=4, ensure_ascii=False)
                self._dirty = False
                self.logger.debug(f"缓存已保存到 {self.cache_file} ({len(self.caches)} 条记录)")
            except Exception as e:
                self.logger.error(f"保存缓存失败: {e}")

    def _safe_save_cache(self):
        """安全保存缓存（用于atexit）"""
        try:
            self.save_cache()
        except:
            pass  # 静默处理退出时的错误

    def __del__(self):
        """析构函数"""
        try:
            if self._dirty:  # 只有在缓存被修改时才保存
                self.save_cache()
        except:
            pass

    # ...existing methods...