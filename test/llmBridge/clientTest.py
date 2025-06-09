import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from py2joern.llmBridge.clients.lamaClient import LlamaClient
from py2joern.llmBridge.models.dataclass import LLMRequest, AnalysisType
from py2joern.llmBridge.models.prompt import FunctionPrompt
from py2joern.models.function import Function


class TestLlamaClient(unittest.TestCase):
    """LlamaClient单元测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.client = LlamaClient(
            base_url="http://test.example.com/api/",
            api_key="test_key",
            model="test_model"
        )
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.client.base_url, "http://test.example.com/api/")
        self.assertEqual(self.client.api_key, "test_key")
        self.assertEqual(self.client.model, "test_model")
    
    @patch('CPGvulnHunter.llmBridge.clients.lamaClient.OpenAI')
    def test_send_request(self, mock_openai):
        """测试发送请求"""
        # 模拟OpenAI响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "测试响应"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 创建测试请求
        request = LLMRequest(
            analysis_type=AnalysisType.CODE_UNDERSTANDING,
            prompt="测试提示词",
            system_content="你是测试助手"
        )
        
        # 重新初始化客户端以使用mock
        client = LlamaClient()
        result = client.send(request)
        
        self.assertEqual(result, "测试响应")
    
    def test_simple_chat(self):
        """测试简单对话"""
        with patch.object(self.client, 'chat_completion') as mock_chat:
            mock_chat.return_value = "Hello World"
            
            result = self.client.simple_chat("Hello")
            
            mock_chat.assert_called_once()
            self.assertEqual(result, "Hello World")
    
    def test_get_available_models_fallback(self):
        """测试获取模型列表的fallback逻辑"""
        with patch.object(self.client.client, 'models') as mock_models:
            mock_models.list.side_effect = Exception("API Error")
            
            models = self.client.get_available_models()
            
            # 应该返回预定义的模型列表
            self.assertIn("qwen2.5-coder-32b-instruct-fp16", models)
            self.assertIsInstance(models, list)


class TestLLMRequest(unittest.TestCase):
    """LLMRequest数据类测试"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        request = LLMRequest(
            analysis_type=AnalysisType.VULNERABILITY_DETECTION,
            prompt="测试提示"
        )
        
        self.assertEqual(request.analysis_type, AnalysisType.VULNERABILITY_DETECTION)
        self.assertEqual(request.prompt, "测试提示")
        self.assertEqual(request.expected_format, "json")
        self.assertIsInstance(request.context, dict)
    
    def test_to_messages(self):
        """测试消息转换"""
        request = LLMRequest(
            analysis_type=AnalysisType.CODE_UNDERSTANDING,
            prompt="测试提示",
            system_content="系统提示"
        )
        
        messages = request.to_messages()
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "系统提示")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "测试提示")
    
    def test_context_operations(self):
        """测试上下文操作"""
        request = LLMRequest(
            analysis_type=AnalysisType.SEMANTIC_RULES,
            prompt="测试"
        )
        
        # 设置上下文值
        request.set_context_value("test_key", "test_value")
        self.assertEqual(request.get_context_value("test_key"), "test_value")
        
        # 获取不存在的键
        self.assertIsNone(request.get_context_value("nonexistent"))
        self.assertEqual(request.get_context_value("nonexistent", "default"), "default")


class TestFunctionPrompt(unittest.TestCase):
    """FunctionPrompt测试"""
    
    def setUp(self):
        """设置测试函数"""
        self.test_function = Function(
            name="strcpy",
            full_name="strcpy",
            signature="char* strcpy(char* dest, const char* src)"
        )
    
    def test_build_semantic_analysis_request(self):
        """测试语义分析请求构建"""
        request = FunctionPrompt.build_semantic_analysis_request(self.test_function)
        
        self.assertIsInstance(request, LLMRequest)
        self.assertEqual(request.analysis_type, AnalysisType.SEMANTIC_RULES)
        self.assertIn("strcpy", request.prompt)
        self.assertIn("function_name", request.context)
    
    def test_build_semantic_analysis_prompt(self):
        """测试语义分析提示词构建"""
        prompt = FunctionPrompt.build_semantic_analysis_prompt(self.test_function)
        
        self.assertIsInstance(prompt, str)
        self.assertIn("strcpy", prompt)
        self.assertIn("数据流", prompt)
        self.assertIn("JSON", prompt)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
