import json
import logging
import hashlib
import time
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
import atexit
import threading

from CPGvulnHunter.models.llm.dataclass import LLMRequest
from CPGvulnHunter.utils.uitils import extract_json_block


class LLMBridge:

    def __init__(self, base_url: str = "", api_key: str = '', model: str = "", 
                 enable_cache: bool = True, cache_dir: str = "llm_cache"):
        """
        初始化LLMBridge
        
        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 默认模型名称
            enable_cache: 是否启用缓存
            cache_dir: 缓存目录路径
        """      
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Ensure logger uses the level from config
        self.logger.setLevel(logging.getLogger().level)
        
        # 缓存相关配置
        self.enable_cache = enable_cache
        self.cache_dir = Path(cache_dir) if enable_cache else None
        
        # 缓存统计
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0
        
        # 内存缓存
        self._memory_cache = {}
        
        # 缓存锁，确保线程安全
        self._cache_lock = threading.RLock()
        
        # 初始化缓存
        if self.enable_cache:
            self._init_cache()

        # 注册退出时保存缓存（使用更安全的方法）
        if self.enable_cache:
            atexit.register(self._safe_shutdown_cache)

    def _init_cache(self):
        """初始化缓存系统"""
        if not self.cache_dir:
            return
            
        try:
            self.cache_dir.mkdir(exist_ok=True, parents=True)
            self.cache_file = self.cache_dir / "llm_responses.pkl"
            self._load_persistent_cache()
            self.logger.info(f"缓存系统初始化完成，缓存目录: {self.cache_dir}")
        except Exception as e:
            self.logger.warning(f"缓存系统初始化失败: {e}")
            self.enable_cache = False

    def _load_persistent_cache(self):
        """从文件加载持久化缓存"""
        if not hasattr(self, 'cache_file') or not self.cache_file:
            return
            
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    self._memory_cache = pickle.load(f)
                self.logger.info(f"加载持久化缓存: {len(self._memory_cache)} 条记录")
        except Exception as e:
            self.logger.warning(f"加载持久化缓存失败: {e}")
            self._memory_cache = {}

    def _save_persistent_cache(self):
        """保存缓存到文件"""
        if not self.enable_cache or not hasattr(self, 'cache_file') or not self.cache_file:
            return
            
        # 检查Python是否正在关闭
        try:
            import sys
            if sys.meta_path is None:
                # Python正在关闭，不进行缓存保存
                return
        except:
            # 如果无法检查系统状态，跳过保存
            return
            
        try:
            with self._cache_lock:
                # 确保目录存在
                self.cache_file.parent.mkdir(exist_ok=True, parents=True)
                
                # 写入临时文件，然后原子性重命名，避免写入过程中出错导致缓存损坏
                temp_file = self.cache_file.with_suffix('.tmp')
                with open(temp_file, 'wb') as f:
                    pickle.dump(self._memory_cache, f)
                
                # 原子性重命名
                temp_file.replace(self.cache_file)
                self.logger.debug(f"缓存已保存到文件: {len(self._memory_cache)} 条记录")
        except Exception as e:
            # 如果是Python关闭相关的错误，静默处理
            if "shutting down" in str(e) or "meta_path" in str(e) or "interpreter" in str(e):
                # Python正在关闭，这是预期的行为，不记录错误
                return
            self.logger.error(f"保存缓存失败: {e}")
            # 如果临时文件存在，删除它
            try:
                temp_file = self.cache_file.with_suffix('.tmp')
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass

    def _generate_cache_key(self, messages: List[Dict[str, str]], 
                          model: str, temperature: float, top_p: float, 
                          max_tokens: int) -> str:
        """
        生成缓存键
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            top_p: top_p参数
            max_tokens: 最大token数
            
        Returns:
            str: 缓存键
        """
        # 创建包含所有关键参数的字符串
        cache_content = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
        
        # 转换为JSON字符串并生成哈希
        content_str = json.dumps(cache_content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """从缓存获取响应"""
        if not self.enable_cache:
            return None
            
        try:
            with self._cache_lock:
                if cache_key in self._memory_cache:
                    cache_entry = self._memory_cache[cache_key]
                    # 更新访问次数和时间戳
                    cache_entry['access_count'] = cache_entry.get('access_count', 0) + 1
                    cache_entry['last_access'] = time.time()
                    
                    self._cache_hits += 1
                    self.logger.debug(f"缓存命中，键: {cache_key[:16]}...")
                    return cache_entry['response']
        except Exception as e:
            self.logger.warning(f"从缓存获取数据失败: {e}")
        
        return None

    def _save_to_cache(self, cache_key: str, response: str):
        """保存响应到缓存"""
        if not self.enable_cache:
            return

        try:
            with self._cache_lock:
                self._memory_cache[cache_key] = {
                    'response': response,
                    'timestamp': time.time(),
                    'last_access': time.time(),
                    'access_count': 1
                }

                # 缓存大小管理：如果缓存过大，清理最老的条目
                self._cleanup_cache_if_needed()

            # 异步保存到文件，避免阻塞
            self._save_persistent_cache()
        except Exception as e:
            self.logger.warning(f"保存缓存失败: {e}")

    def _cleanup_cache_if_needed(self, max_cache_size: int = 1000000):
        """如果缓存过大，清理最老的条目"""
        if len(self._memory_cache) <= max_cache_size:
            return
            
        try:
            # 按最后访问时间排序，删除最老的条目
            sorted_items = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1].get('last_access', 0)
            )
            
            # 删除最老的20%条目
            items_to_remove = int(len(sorted_items) * 0.2)
            for i in range(items_to_remove):
                cache_key = sorted_items[i][0]
                del self._memory_cache[cache_key]
            
            self.logger.info(f"清理了 {items_to_remove} 个缓存条目，当前缓存大小: {len(self._memory_cache)}")
        except Exception as e:
            self.logger.warning(f"清理缓存失败: {e}")

    def send(self, request: LLMRequest, returnJson: bool = True) -> Union[dict, str]:
        """
        发送请求并获取响应（带缓存）
        
        Args:
            request: LLMRequest对象，包含分析类型、上下文和提示词
            returnJson: 是否返回JSON格式
            
        Returns:
            Union[dict, str]: 解析后的响应数据或原始文本
        """
        self._total_requests += 1
        
        messages = request.to_messages()
        
        # 生成缓存键
        cache_key = self._generate_cache_key(
            messages=messages,
            model=self.model,
            temperature=0.1,  # 使用默认参数
            top_p=0.1,
            max_tokens=4000
        )
        
        # 尝试从缓存获取
        cached_response = self._get_from_cache(cache_key)
        if cached_response is not None:
            self.logger.debug("使用缓存响应")
            if returnJson:
                self.logger.debug(cached_response)
                return extract_json_block(cached_response)
            else:
                return cached_response
        
        # 缓存未命中，发送实际请求
        self._cache_misses += 1
        self.logger.debug("缓存未命中，发送LLM请求")
        
        response_text = self.chat_completion(messages, model=self.model)
        
        # 保存到缓存
        self._save_to_cache(cache_key, response_text)
        self.logger.debug(response_text)
        if returnJson:
            return extract_json_block(response_text)
        else:
            return response_text

    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = '',
                       temperature: float = 0.1,
                       top_p: float = 0.1,
                       max_tokens: int = 4000) -> str:
        """
        进行聊天完成
        
        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant", "content": "..."}]
            model: 使用的模型名称，如果为None则使用默认模型
            temperature: 温度参数
            top_p: top_p参数
            max_tokens: 最大token数
            
        Returns:
            str: 模型的回复内容
        """
        # 检查是否有缓存（用于直接调用chat_completion的情况）
        if self.enable_cache:
            cache_key = self._generate_cache_key(messages, model, temperature, top_p, max_tokens)
            cached_response = self._get_from_cache(cache_key)
            if cached_response is not None:
                self.logger.debug("chat_completion缓存命中")
                return cached_response
            
            self._cache_misses += 1
            
        try:
            self.logger.debug(f"发送消息: {len(messages)} 条消息")
            self.logger.debug(f"使用模型: {model}, 温度: {temperature}, top_p: {top_p}, 最大token数: {max_tokens}")
            
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            request_time = time.time() - start_time
            self.logger.debug(f"LLM请求完成，耗时: {request_time:.2f}秒")
            
            response_text = response.choices[0].message.content
            
            # 保存到缓存（如果启用了缓存）
            if self.enable_cache:
                cache_key = self._generate_cache_key(messages, model, temperature, top_p, max_tokens)
                self._save_to_cache(cache_key, response_text)
            
            return response_text
            
        except Exception as e:
            raise Exception(f"聊天完成请求失败: {str(e)}")

    def _safe_shutdown_cache(self):
        """安全地关闭缓存系统，处理Python关闭时的状态"""
        try:
            # 尝试保存缓存，但不记录关闭相关的错误
            self._save_persistent_cache()
        except:
            # 在Python关闭时，任何错误都被静默处理
            # 避免在程序退出时显示令人困惑的错误消息
            pass

    def manual_save_cache(self):
        """手动保存缓存（供用户主动调用）"""
        if not self.enable_cache:
            return False
        try:
            self._save_persistent_cache()
            return True
        except Exception as e:
            self.logger.error(f"手动保存缓存失败: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_enabled": self.enable_cache,
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": self._cache_hits / max(self._total_requests, 1),
            "cache_size": len(self._memory_cache) if self.enable_cache else 0
        }

    def clear_cache(self):
        """清空所有缓存"""
        try:
            with self._cache_lock:
                self._memory_cache.clear()
                self._cache_hits = 0
                self._cache_misses = 0
                self._total_requests = 0
                
                if hasattr(self, 'cache_file') and self.cache_file and self.cache_file.exists():
                    self.cache_file.unlink()
                
                self.logger.info("LLM缓存已清空")
        except Exception as e:
            self.logger.error(f"清空缓存失败: {e}")

    def disable_cache(self):
        """禁用缓存"""
        self.enable_cache = False
        self.logger.info("LLM缓存已禁用")

    def enable_cache_func(self):
        """启用缓存"""
        self.enable_cache = True
        self._init_cache()
        self.logger.info("LLM缓存已启用")

    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            List[str]: 可用模型名称列表
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            self.logger.error(f"获取模型列表失败: {e}")
            return []

    def __del__(self):
        """析构时保存缓存"""
        try:
            if self.enable_cache and hasattr(self, '_memory_cache'):
                self._save_persistent_cache()
        except:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjBjN2ZjYWI0LWNkYTctNDQ5MC04Y2VkLThmZDNjNDQ0ODM4MyJ9.EF4VyeqVO0rfgN5mpFWYYZEaarcOXSQ1vjw-UYVCfkI"
    # 测试LlamaClient

    client = LLMBridge("http://192.168.5.253:3000/api/",api_key=key,model="qwen2.5:14b")
    
    # 获取可用模型
    models = client.get_available_models()
    print("可用模型:", models)
    
    # 创建测试请求
    request = LLMRequest(
        system_content="你是一位程序静态分析专家，擅长理解代码的语义并分析数据流向，并以json格式返回结果",
        prompt="请分析以下代码的功能：\n\n```c\n#include <stdio.h>\nint main() {\n    printf(\"Hello, World!\");\n    return 0;\n}\n```"
    )
    response = client.send(request)

    print("响应结果:", response)