import logging
import json
import re
from typing import Union

def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本: {text}")
    logging.error(f"文本repr: {repr(text)}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本前200字符: {text[:200]}")
    logging.error(f"文本repr: {repr(text[:100])}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise


def extract_json_block(text: str) -> Union[dict, list]:
    """
    从文本中提取JSON内容，支持多种格式：
    1. 直接的JSON字符串
    2. ```json ... ``` 代码块
    3. ``` ... ``` 代码块
    4. 文本中嵌入的JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Union[dict, list]: 解析后的json对象
        
    Raises:
        ValueError: 当无法找到有效JSON时
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")
    
    # 清理文本
    text_cleaned = text.strip()
    logging.debug(f"正在提取JSON，原始文本长度: {len(text)}, 清理后长度: {len(text_cleaned)}")
    
    # 1. 首先尝试直接解析整个文本
    if text_cleaned.startswith('{') or text_cleaned.startswith('['):
        try:
            json_content = json.loads(text_cleaned)  # 验证JSON有效性
            logging.debug("直接解析成功")
            return json_content
        except json.JSONDecodeError as e:
            logging.debug(f"直接解析失败: {e}")
    
    # 2. 尝试提取代码块中的JSON
    patterns = [
        r'```json\s*(.*?)\s*```',      # ```json ... ```
        r'```\s*json\s*(.*?)\s*```',   # ``` json ... ```
        r'```\s*(.*?)\s*```',          # ``` ... ```
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            content = match.strip()
            logging.debug(f"模式 {i+1} 找到内容: {content[:100]}...")
            
            if content.startswith('{') or content.startswith('['):
                try:
                    content = json.loads(content)  # 验证JSON有效性
                    logging.debug(f"模式 {i+1} 解析成功")
                    return content
                except json.JSONDecodeError as e:
                    logging.debug(f"模式 {i+1} JSON无效: {e}")
                    continue
    
    # 3. 尝试查找文本中的JSON对象（更智能的匹配）
    json_patterns = [
        r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # 简单的嵌套JSON对象
        r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'  # JSON数组
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                json_content = json.loads(match)
                logging.debug(f"找到嵌入JSON: {match[:100]}...")
                return json_content
            except json.JSONDecodeError:
                continue
    
    # 4. 最后尝试更宽松的匹配（处理可能的格式问题）
    # 移除可能的控制字符和多余的空白
    cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 规范化空白字符
    
    # 再次尝试查找JSON
    json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1).strip()
            json_content = json.loads(candidate)  # 解析并返回JSON对象
            logging.debug("宽松匹配成功")
            return json_content
        except json.JSONDecodeError:
            pass
    
    # 如果所有方法都失败，提供详细的错误信息
    logging.error(f"无法提取JSON，原始文本: {text}")
    raise ValueError(f"在文本中未找到有效的JSON内容。文本长度: {len(text)}")


def safe_json_loads(text: str) -> dict:
    """
    安全的JSON加载函数，包含更多的容错处理
    
    Args:
        text: JSON字符串
        
    Returns:
        dict: 解析后的JSON对象
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # 尝试修复常见的JSON格式问题
        fixed_text = text
        
        # 修复单引号问题
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
        fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)
        
        # 修复尾部逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            logging.error(f"JSON修复失败，原始错误: {e}")
            raise