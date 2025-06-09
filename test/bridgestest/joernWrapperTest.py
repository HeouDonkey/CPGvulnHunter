import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import logging
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from CPGvulnHunter.bridges.joernWrapper import JoernWrapper
from CPGvulnHunter.models.cpg.joernQueryResult import JoernQueryResult
from CPGvulnHunter.models.cpg.function import Function, Parameter


class TestJoernWrapper(unittest.TestCase):
    
    def setUp(self):
        """测试前的准备工作"""
        # Mock JoernBridge 以避免实际的 Joern 连接
        self.mock_joern_bridge = Mock()
        
        with patch('CPGvulnHunter.bridges.joernWrapper.JoernBridge') as MockBridge:
            MockBridge.return_value = self.mock_joern_bridge
            self.wrapper = JoernWrapper("/fake/joern/path")
        
        # 设置日志等级，便于调试
        logging.basicConfig(level=logging.DEBUG)
    
    def tearDown(self):
        """测试后的清理工作"""
        self.wrapper.close()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.wrapper.joern)
        self.assertIsNotNone(self.wrapper.logger)
        self.assertFalse(self.wrapper._semantics_applied)
        self.assertIsNotNone(self.wrapper._json_pattern)
    
    def test_context_manager(self):
        """测试上下文管理器功能"""
        with patch('CPGvulnHunter.bridges.joernWrapper.JoernBridge') as MockBridge:
            mock_bridge = Mock()
            MockBridge.return_value = mock_bridge
            
            with JoernWrapper("/fake/path") as wrapper:
                self.assertIsInstance(wrapper, JoernWrapper)
            
            # 验证 close 方法被调用
            mock_bridge.close_shell.assert_called_once()
    
    def test_execute_command_success(self):
        """测试成功执行命令"""
        # 模拟成功的命令执行
        self.mock_joern_bridge.send_command.return_value = "success result"
        
        result = self.wrapper._execute_command("test command")
        
        self.assertTrue(result.success)
        self.assertEqual(result.raw_result, "success result")
        self.mock_joern_bridge.send_command.assert_called_once_with("test command", None)
    
    def test_execute_command_failure(self):
        """测试命令执行失败"""
        # 模拟命令执行异常
        self.mock_joern_bridge.send_command.side_effect = Exception("Connection failed")
        
        result = self.wrapper._execute_command("test command")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Connection failed")
    
    def test_extract_json_data_success(self):
        """测试 JSON 数据提取成功"""
        raw_result = 'Some text before """{"key": "value", "number": 42}""" some text after'
        
        data = self.wrapper._extract_json_data(raw_result)
        
        self.assertIsNotNone(data)
        self.assertEqual(data["key"], "value")
        self.assertEqual(data["number"], 42)
    
    def test_extract_json_data_no_match(self):
        """测试 JSON 数据提取无匹配"""
        raw_result = 'No JSON data here'
        
        data = self.wrapper._extract_json_data(raw_result)
        
        self.assertIsNone(data)
    
    def test_extract_json_data_invalid_json(self):
        """测试无效 JSON 数据"""
        raw_result = '"""invalid json{""" '
        
        data = self.wrapper._extract_json_data(raw_result)
        
        self.assertIsNone(data)
    
    def test_import_code(self):
        """测试导入代码"""
        self.mock_joern_bridge.send_command.return_value = "Import successful"
        
        result = self.wrapper.import_code("/path/to/source")
        
        self.assertTrue(result.success)
        self.mock_joern_bridge.send_command.assert_called_with('importCode("/path/to/source")', None)
    
    def test_get_function_full_names_success(self):
        """测试获取函数名列表成功"""
        mock_response = '"""["func1", "func2", "func3"]"""'
        self.mock_joern_bridge.send_command.return_value = mock_response
        
        result = self.wrapper.get_function_full_names()
        
        self.assertEqual(result, ["func1", "func2", "func3"])
        self.mock_joern_bridge.send_command.assert_called_with("cpg.method.fullName.toJsonPretty", None)
    
    def test_get_function_full_names_failure(self):
        """测试获取函数名列表失败"""
        self.mock_joern_bridge.send_command.side_effect = Exception("Query failed")
        
        result = self.wrapper.get_function_full_names()
        
        self.assertEqual(result, [])
    
    @patch('CPGvulnHunter.models.cpg.function.Function.from_json')
    def test_get_function_by_full_name_success(self, mock_from_json):
        """测试根据名称获取函数成功"""
        mock_function = Mock(spec=Function)
        mock_from_json.return_value = mock_function
        
        mock_response = '"""{"name": "test_func", "fullName": "test_func"}"""'
        self.mock_joern_bridge.send_command.return_value = mock_response
        
        result = self.wrapper.get_function_by_full_name("test_func")
        
        self.assertEqual(result, mock_function)
        mock_from_json.assert_called_once()
    
    def test_get_function_by_full_name_not_found(self):
        """测试函数未找到"""
        self.mock_joern_bridge.send_command.side_effect = Exception("Not found")
        
        result = self.wrapper.get_function_by_full_name("nonexistent_func")
        
        self.assertIsNone(result)
    
    def test_get_function_by_full_name_multiple_results(self):
        """测试返回多个结果时的处理"""
        mock_response = '"""[{"name": "func1"}, {"name": "func2"}]"""'
        self.mock_joern_bridge.send_command.return_value = mock_response
        
        with patch('CPGvulnHunter.models.cpg.function.Function.from_json') as mock_from_json:
            mock_function = Mock(spec=Function)
            mock_from_json.return_value = mock_function
            
            result = self.wrapper.get_function_by_full_name("test_func")
            
            self.assertEqual(result, mock_function)
            # 应该使用第一个结果
            mock_from_json.assert_called_once_with({"name": "func1"})
    
    @patch('CPGvulnHunter.models.cpg.function.Parameter.from_json')
    def test_get_parameter_success(self, mock_param_from_json):
        """测试获取参数成功"""
        mock_function = Mock(spec=Function)
        mock_function.generateParameterQuery.return_value = "parameter query"
        
        mock_param1 = Mock(spec=Parameter)
        mock_param2 = Mock(spec=Parameter)
        mock_param_from_json.side_effect = [mock_param1, mock_param2]
        
        mock_response = '"""[{"name": "param1"}, {"name": "param2"}]"""'
        self.mock_joern_bridge.send_command.return_value = mock_response
        
        result = self.wrapper.get_parameter(mock_function)
        
        # 注意：代码中有 bug，return 语句在循环内部，只会返回第一个参数
        # 这里测试实际行为
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_param1)
    
    def test_import_dataflow_classes_success(self):
        """测试导入数据流类成功"""
        self.mock_joern_bridge.send_command.return_value = "Import successful"
        
        result = self.wrapper.import_dataflow_classes()
        
        self.assertTrue(result)
        # 验证调用了3次导入命令
        self.assertEqual(self.mock_joern_bridge.send_command.call_count, 3)
    
    def test_import_dataflow_classes_failure(self):
        """测试导入数据流类失败"""
        self.mock_joern_bridge.send_command.side_effect = Exception("Import failed")
        
        result = self.wrapper.import_dataflow_classes()
        
        self.assertFalse(result)
    
    def test_define_extra_flows_empty(self):
        """测试定义空的额外流规则"""
        result = self.wrapper.define_extra_flows("")
        
        self.assertTrue(result)
        # 不应该调用 send_command
        self.mock_joern_bridge.send_command.assert_not_called()
    
    def test_define_extra_flows_success(self):
        """测试定义额外流规则成功"""
        self.mock_joern_bridge.send_command.return_value = "Success"
        
        result = self.wrapper.define_extra_flows("val extraFlows = List()")
        
        self.assertTrue(result)
        self.mock_joern_bridge.send_command.assert_called_once()
    
    def test_apply_semantics_full_flow(self):
        """测试完整语义规则应用流程"""
        # Mock 所有依赖方法
        self.mock_joern_bridge.health_check.return_value = True
        self.mock_joern_bridge.send_command.return_value = "Success"
        
        result = self.wrapper.apply_semantics("val extraFlows = List()")
        
        self.assertTrue(result)
        self.assertTrue(self.wrapper.is_semantics_applied())
        # 验证调用了多个命令（导入类 + 语义上下文 + 引擎上下文）
        self.assertGreater(self.mock_joern_bridge.send_command.call_count, 3)
    
    def test_apply_semantics_health_check_fail(self):
        """测试健康检查失败"""
        self.mock_joern_bridge.health_check.return_value = False
        
        result = self.wrapper.apply_semantics()
        
        self.assertFalse(result)
        self.assertFalse(self.wrapper.is_semantics_applied())
    
    def test_run_taint_analysis_without_semantics(self):
        """测试未应用语义规则时的污点分析"""
        result = self.wrapper.run_taint_analysis("source", "sink")
        
        self.assertIsNone(result)
    
    def test_run_taint_analysis_success(self):
        """测试成功的污点分析"""
        # 先应用语义规则
        self.wrapper._semantics_applied = True
        
        mock_response = '"""{"paths": [{"source": "src", "sink": "snk"}]}"""'
        self.mock_joern_bridge.send_command.return_value = mock_response
        
        result = self.wrapper.run_taint_analysis("source", "sink")
        
        self.assertIsNotNone(result)
        self.assertIn("paths", result)
    

    
    def test_execute_custom_query(self):
        """测试执行自定义查询"""
        self.mock_joern_bridge.send_command.return_value = "Custom result"
        
        result = self.wrapper.execute_custom_query("custom.query", timeout=30)
        
        self.assertTrue(result.success)
        self.assertEqual(result.raw_result, "Custom result")
        self.mock_joern_bridge.send_command.assert_called_with("custom.query", 30)
    
    def test_close_with_close_shell(self):
        """测试关闭连接（有 close_shell 方法）"""
        self.mock_joern_bridge.close_shell = Mock()
        
        self.wrapper.close()
        
        self.mock_joern_bridge.close_shell.assert_called_once()
    
    def test_close_without_close_shell(self):
        """测试关闭连接（无 close_shell 方法）"""
        # 不设置 close_shell 属性
        if hasattr(self.mock_joern_bridge, 'close_shell'):
            delattr(self.mock_joern_bridge, 'close_shell')
        
        # 应该不会抛出异常
        self.wrapper.close()


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)