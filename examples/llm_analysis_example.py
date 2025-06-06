#!/usr/bin/env python3
"""
LLM辅助漏洞检测示例
演示如何使用VulnerabilityLLMBridge进行智能化的静态代码分析
"""

import sys
import os
import logging
from typing import List

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from py2joern.cpgs.cpg import CPG
from py2joern.llmBridge.llmBridge import VulnerabilityLLMBridge, LLMBridge
from py2joern.models.flowPath import DataFlowResult

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockLLMClient:
    """
    模拟LLM客户端，用于演示
    在实际使用中，可以替换为真实的LLM客户端(OpenAI, Claude等)
    """
    
    def __init__(self):
        self.model = "mock-gpt-4"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """模拟生成响应"""
        if "语义规则" in prompt or "semantic" in prompt.lower():
            return self._generate_semantic_rules()
        elif "源" in prompt and "汇聚" in prompt:
            return self._generate_sources_sinks()
        elif "漏洞" in prompt or "vulnerability" in prompt.lower():
            return self._generate_vulnerability_analysis()
        else:
            return "这是一个模拟的LLM响应"
    
    def _generate_semantic_rules(self) -> str:
        """生成模拟的语义规则"""
        return '''```json
        {
            "semantic_rules": [
                {
                    "method_pattern": "^.*strcpy$",
                    "param_flows": [[2, 1]],
                    "is_regex": true,
                    "confidence": 0.9,
                    "reasoning": "strcpy将源字符串复制到目标缓冲区，数据从第2个参数流向第1个参数"
                },
                {
                    "method_pattern": "^.*strncpy$", 
                    "param_flows": [[2, 1]],
                    "is_regex": true,
                    "confidence": 0.9,
                    "reasoning": "strncpy安全地复制字符串，数据从源参数流向目标参数"
                },
                {
                    "method_pattern": "^.*fgets$",
                    "param_flows": [[-1, 1]],
                    "is_regex": true,
                    "confidence": 0.8,
                    "reasoning": "fgets从文件读取数据到缓冲区，返回值指向目标缓冲区"
                }
            ]
        }
        ```'''
    
    def _generate_sources_sinks(self) -> str:
        """生成模拟的源/汇聚点识别"""
        return '''```json
        {
            "sources": [
                {
                    "function_name": "input",
                    "parameter_index": -1,
                    "source_type": "用户输入",
                    "confidence": 0.9,
                    "reasoning": "input函数通过返回值提供用户输入数据"
                },
                {
                    "function_name": "fgets",
                    "parameter_index": 1,
                    "source_type": "文件输入",
                    "confidence": 0.8,
                    "reasoning": "fgets从文件/标准输入读取数据到第一个参数指向的缓冲区"
                }
            ],
            "sinks": [
                {
                    "function_name": "dangerous_sink",
                    "parameter_index": 1,
                    "sink_type": "危险操作",
                    "vulnerability_types": ["任意代码执行", "数据泄露"],
                    "confidence": 0.95,
                    "reasoning": "dangerous_sink函数处理可能不受信任的数据，存在安全风险"
                },
                {
                    "function_name": "printf",
                    "parameter_index": 1,
                    "sink_type": "格式化输出",
                    "vulnerability_types": ["格式化字符串漏洞"],
                    "confidence": 0.7,
                    "reasoning": "printf的格式化字符串如果来自用户输入可能导致漏洞"
                }
            ]
        }
        ```'''
    
    def _generate_vulnerability_analysis(self) -> str:
        """生成模拟的漏洞分析"""
        return '''```json
        {
            "is_vulnerable": true,
            "vulnerability_type": "缓冲区溢出",
            "severity": "高",
            "confidence": 0.85,
            "attack_vector": "攻击者可以通过输入超长字符串导致缓冲区溢出",
            "impact": "可能导致程序崩溃或任意代码执行",
            "remediation": "使用strncpy代替strcpy，并确保目标缓冲区足够大",
            "cwe_ids": ["CWE-120", "CWE-787"],
            "reasoning": "数据流从不受信任的输入源流向了危险的字符串操作函数，且缺乏适当的边界检查"
        }
        ```'''

class OpenAIMockClient:
    """
    模拟OpenAI风格的客户端
    """
    class Chat:
        class Completions:
            def create(self, **kwargs):
                class Choice:
                    class Message:
                        content = MockLLMClient()._generate_semantic_rules()
                    message = Message()
                class Response:
                    choices = [Choice()]
                return Response()
        completions = Completions()
    chat = Chat()

def demonstrate_llm_analysis():
    """演示LLM辅助分析功能"""
    
    print("=" * 60)
    print("LLM辅助漏洞检测演示")
    print("=" * 60)
    
    # 1. 初始化LLM客户端和分析器
    print("\n1. 初始化LLM分析器...")
    
    # 可以使用不同类型的LLM客户端
    # mock_client = MockLLMClient()  # 简单模拟客户端
    openai_mock = OpenAIMockClient()  # OpenAI风格客户端
    
    # 创建分析器
    vulnerability_analyzer = VulnerabilityLLMBridge(
        llm_client=openai_mock,
        config={
            "model": "gpt-4",
            "max_tokens": 2048,
            "temperature": 0.1
        }
    )
    
    print("✓ LLM分析器初始化完成")
    
    # 2. 创建CPG并获取函数信息
    print("\n2. 分析代码并构建CPG...")
    
    test_src = "/home/nstl/data/vuln_hunter/py2joern/test/test_case/test1"
    
    try:
        cpg = CPG(test_src)
        print(f"✓ CPG构建完成，发现 {len(cpg.functions)} 个函数")
        print(f"  - 外部函数: {len(cpg.external_functions)}")
        print(f"  - 内部函数: {len(cpg.internal_functions)}")
        
        # 3. 使用LLM分析外部函数并生成语义规则
        print("\n3. 使用LLM分析外部函数...")
        
        semantics = vulnerability_analyzer.analyze_external_functions(cpg.external_functions)
        print(f"✓ 生成了 {len(semantics.rules)} 条语义规则")
        
        for i, rule in enumerate(semantics.rules, 1):
            print(f"  规则{i}: {rule.method_full_name} -> {rule.param_flows}")
        
        # 4. 识别源和汇聚点
        print("\n4. 识别潜在的源和汇聚点...")
        
        sources, sinks = vulnerability_analyzer.identify_sources_and_sinks(cpg.internal_functions)
        print(f"✓ 识别到 {len(sources)} 个数据源, {len(sinks)} 个汇聚点")
        
        for source in sources:
            print(f"  源: {source.name} (索引: {source.index})")
        
        for sink in sinks:
            print(f"  汇聚: {sink.name} (索引: {sink.index})")
        
        # 5. 执行数据流分析
        print("\n5. 执行数据流分析...")
        
        cpg.apply_semantics(semantics)
        print("✓ 数据流分析完成")
        
        # 6. 分析数据流路径的漏洞风险
        print("\n6. 分析数据流路径...")
        
        # 模拟一些数据流路径
        mock_flow_data = '''[
        {
            "path": [
                {
                    "node": {
                        "name": "input",
                        "_id": 1,
                        "code": "input()",
                        "_label": "CALL",
                        "lineNumber": 20
                    },
                    "visible": true,
                    "isOutputArg": false,
                    "outEdgeLabel": ""
                },
                {
                    "node": {
                        "name": "dangerous_sink", 
                        "_id": 2,
                        "code": "dangerous_sink(data)",
                        "_label": "CALL",
                        "lineNumber": 30
                    },
                    "visible": true,
                    "isOutputArg": false,
                    "outEdgeLabel": ""
                }
            ]
        }
        ]'''
        
        flow_result = DataFlowResult.from_joern_result(mock_flow_data)
        analyzed_paths = vulnerability_analyzer.analyze_vulnerability_paths(flow_result.flows)
        
        print(f"✓ 分析了 {len(analyzed_paths)} 条数据流路径")
        
        for i, path in enumerate(analyzed_paths, 1):
            print(f"  路径{i}: 漏洞风险={path.is_vulnerable}, 类型={path.vulnerability_type}")
        
        # 7. 生成安全报告
        print("\n7. 生成安全分析报告...")
        
        analysis_results = {
            "total_functions": len(cpg.functions),
            "external_functions": len(cpg.external_functions), 
            "internal_functions": len(cpg.internal_functions),
            "semantic_rules": len(semantics.rules),
            "identified_sources": len(sources),
            "identified_sinks": len(sinks),
            "analyzed_paths": len(analyzed_paths),
            "vulnerable_paths": len([p for p in analyzed_paths if p.is_vulnerable])
        }
        
        report = vulnerability_analyzer.generate_security_report(analysis_results)
        print("✓ 安全报告生成完成")
        print("\n报告预览:")
        print(report[:500] + "..." if len(report) > 500 else report)
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        print(f"❌ 分析失败: {e}")

def demonstrate_code_explanation():
    """演示代码解释功能"""
    
    print("\n" + "=" * 60)
    print("代码解释功能演示")
    print("=" * 60)
    
    mock_client = MockLLMClient()
    analyzer = VulnerabilityLLMBridge(mock_client)
    
    # 示例代码片段
    code_snippet = '''
    char* input() {
        char data[100];
        fgets(data, 100, stdin);
        return data;
    }
    '''
    
    explanation = analyzer.explain_code_behavior(
        code_snippet=code_snippet,
        context="这是一个从标准输入读取数据的函数"
    )
    
    print("代码解释结果:")
    print(explanation)

def demonstrate_backward_compatibility():
    """演示向后兼容性"""
    
    print("\n" + "=" * 60)
    print("向后兼容性演示")
    print("=" * 60)
    
    # 使用原有的简单接口
    mock_client = MockLLMClient()
    bridge = LLMBridge(mock_client)
    
    # 原有功能仍然可用
    code = bridge.generate_code("写一个安全的字符串复制函数")
    print(f"生成的代码: {code}")
    
    # 新功能也可以通过代理访问
    # (这里需要实际的函数参数，这只是演示接口)
    print("新功能通过原接口也可访问")

if __name__ == "__main__":
    print("LLM辅助漏洞检测系统演示")
    print("=" * 60)
    
    try:
        # 演示主要功能
        demonstrate_llm_analysis()
        
        # 演示代码解释
        demonstrate_code_explanation()
        
        # 演示向后兼容
        demonstrate_backward_compatibility()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        
    except KeyboardInterrupt:
        print("\n用户中断演示")
    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"演示失败: {e}")
