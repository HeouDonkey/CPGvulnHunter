from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """LLM 配置数据类"""
    base_url: str = "http://localhost:11434"
    api_key: str = ""
    model: str = "qwen2.5-coder:32b"
    timeout: int = 30
    max_tokens: int = 4096
    temperature: float = 0.7