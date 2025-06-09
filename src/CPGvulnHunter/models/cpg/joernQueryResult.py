import json
import re
import logging
from typing import Any, Optional


class JoernQueryResult:
    """Joern查询结果包装类"""
    
    def __init__(self, raw_result: str, success: bool = True, error_message: str = ""):
        self.raw_result = raw_result
        self.success = success
        self.error_message = error_message
        self._parsed_data = None
    
    def get_json_data(self) -> Optional[Any]:
        """解析JSON数据"""
        if self._parsed_data is not None:
            return self._parsed_data
        
        match = re.search(r'"""(.*?)"""', self.raw_result, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                self._parsed_data = json.loads(json_str)
                return self._parsed_data
            except json.JSONDecodeError as e:
                logging.error(f"JSON解析失败: {e}")
                return None
        return None
    
    def has_error(self) -> bool:
        """检查是否有错误"""
        return not self.success or "error" in self.raw_result.lower() or "exception" in self.raw_result.lower()