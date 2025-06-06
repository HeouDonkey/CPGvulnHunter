from abc import ABC, abstractmethod

from py2joern.llmBridge.models.dataclass import LLMRequest

class Client(ABC):
    """
    客户端基类，定义了统一的接口和基本功能
    """

    def __init__(self, model_name: str, **kwargs):
        self.client_name = model_name  
        self.client =None 


    def send(self, prompt: LLMRequest, **kwargs) -> str:
        """
        发送请求并获取响应

        :param prompt: 输入提示词
        :param kwargs: 额外参数
        :return: 生成的文本
        """
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """
        获取模型信息

        :return: 模型信息字典
        """
        pass