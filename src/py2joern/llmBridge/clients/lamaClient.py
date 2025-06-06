import json
from openai import OpenAI
from typing import List, Dict, Any, Optional

from py2joern.llmBridge.models.dataclass import LLMRequest
import logging

from py2joern.utils.uitils import extract_json_block

"""
{"data":[{"id":"qwen2.5-coder-32b-instruct-fp16","created":1741935394,"object":"model","owned_by":"openai","meta":null,"name":"qwen2.5-coder-32b-instruct-fp16","openai":{"id":"qwen2.5-coder-32b-instruct-fp16","created":1741935394,"object":"model","owned_by":"gpustack","meta":null},"urlIdx":0,"actions":[],"tags":[]},{"id":"DeepSeek-R1-70B-F16","created":1741916860,"object":"model","owned_by":"openai","meta":null,"name":"DeepSeek-R1-70B-F16","openai":{"id":"DeepSeek-R1-70B-F16","created":1741916860,"object":"model","owned_by":"gpustack","meta":null},"urlIdx":0,"actions":[],"tags":[]},{"id":"Llama-3.2-3B-Instruct-Q8_0","created":1742904098,"object":"model","owned_by":"openai","meta":null,"name":"Llama-3.2-3B-Instruct-Q8_0","openai":{"id":"Llama-3.2-3B-Instruct-Q8_0","created":1742904098,"object":"model","owned_by":"gpustack","meta":null},"urlIdx":0,"actions":[],"tags":[]},{"id":"Qwen3-30B-A3B","created":1745989987,"object":"model","owned_by":"openai","meta":null,"name":"Qwen3-30B-A3B","openai":{"id":"Qwen3-30B-A3B","created":1745989987,"object":"model","owned_by":"gpustack","meta":null},"urlIdx":0,"actions":[],"tags":[]},{"id":"1111","name":"漏洞挖掘实验","object":"model","created":1748919353,"owned_by":"openai","info":{"id":"1111","user_id":"0c7fcab4-cda7-4490-8ced-8fd3c4448383","base_model_id":"qwen2.5-coder-32b-instruct-fp16","name":"漏洞挖掘实验","params":{},"meta":{"profile_image_url":"/static/favicon.png","description":null,"capabilities":{"vision":true,"usage":false,"citations":true},"suggestion_prompts":null,"tags":[]},"access_control":null,"is_active":true,"updated_at":1748919353,"created_at":1748919353},"preset":true,"actions":[],"tags":[]}]}
"""

class LamaClient:

    def __init__(self, base_url: str = "http://192.168.5.253/:3000/api/", api_key: str = None,model  = "qwen2.5-coder:32b"):
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
        response_text = self.chat_completion(messages)
        if returnJson:
            # 尝试多种解析策略
            jsonContent = extract_json_block(response_text)
            return jsonContent
        else:
            return response_text
    
   

    def chat_completion(self, 
                   messages: List[Dict[str, str]], 
                   model: str = None,
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
        if model is None:
            model = self.model
            logging.info(f"使用默认模型: {model}")
            
        try:
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
    client = LamaClient("http://192.168.5.253:3000/api/",api_key=key)
    
    # 获取可用模型
    models = client.get_available_models()
    print("可用模型:", models)
    
    request = LLMRequest(
        analysis_type="CODE_UNDERSTANDING",
        system_content="你是一位程序静态分析专家，擅长理解代码的语义并分析数据流向，并以json格式返回结果",
        prompt="请分析以下代码的功能：\n\n```c\n#include <stdio.h>\nint main() {\n    printf(\"Hello, World!\");\n    return 0;\n}\n```"
    )
    response = client.send(request)

    print( response)