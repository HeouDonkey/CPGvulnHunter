import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

from CPGvulnHunter.models.llm.dataclass import LLMRequest
from CPGvulnHunter.utils.uitils import extract_json_block


class LLMBridge:

    def __init__(self, base_url: str = "", api_key: str = '', model: str = ""):
        """
        初始化LlamaClient
        """      
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def send(self, request: LLMRequest,returnJson:bool = True) -> dict:
        """
        发送请求并获取响应
        
        Args:
            request: LLMRequest对象，包含分析类型、上下文和提示词
            
        Returns:
            dict: 解析后的响应数据
        """
        messages = request.to_messages()
        response_text = self.chat_completion(messages,model=self.model)
        if returnJson:
            # 尝试多种解析策略
            jsonContent = extract_json_block(response_text)
            return jsonContent
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
            
        try:
            logging.debug(f"发送消息: {messages}")
            logging.debug(f"使用模型: {model}, 温度: {temperature}, top_p: {top_p}, 最大token数: {max_tokens}")
            response = self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                messages=messages,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"聊天完成请求失败: {str(e)}")

    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            List[str]: 可用模型名称列表
        """
        models = self.client.models.list()
        return [model.id for model in models.data]


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