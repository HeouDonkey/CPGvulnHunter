#!/usr/bin/env python3
"""
集成LLM分析的智能漏洞检测流程
在原有的mainTest.py基础上增加LLM辅助分析功能
"""

import logging
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from py2joern.cpgs.cpg import CPG
from py2joern.models.function import Function
from py2joern.models.semantics import Semantics
from py2joern.models.sink import Sink
from py2joern.models.source import Source
from py2joern.llmBridge.llmBridge import VulnerabilityLLMBridge
from py2joern.llmBridge.config import create_llm_client, LLMConfig, LLMProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

class MockLLMForIntegration:
    """集成测试用的模拟LLM客户端"""
    
    def generate(self, prompt: str, **kwargs) -> str:
        """根据提示词类型返回相应的模拟响应"""
        
        if "语义规则" in prompt or "semantic" in prompt.lower():
            return '''```json
            {
                "semantic_rules": [
                    {
                        "method_pattern": "strncpy",
                        "param_flows": [[2, 1]],
                        "is_regex": false,
                        "confidence": 0.9,
                        "reasoning": "strncpy将源字符串安全地复制到目标缓冲区"
                    },
                    {
                        "method_pattern": "^.*fgets$",
                        "param_flows": [[3, 1]],
                        "is_regex": true,
                        "confidence": 0.8,
                        "reasoning": "fgets从输入流读取数据到缓冲区"
                    }
                ]
            }
            ```'''
        
        elif "源" in prompt and "汇聚" in prompt:
            return '''```json
            {
                "sources": [
                    {
                        "function_name": "input",
                        "parameter_index": -1,
                        "source_type": "用户输入",
                        "confidence": 0.95,
                        "reasoning": "input函数返回用户输入的数据"
                    }
                ],
                "sinks": [
                    {
                        "function_name": "dangerous_sink",
                        "parameter_index": 1,
                        "sink_type": "危险操作",
                        "vulnerability_types": ["缓冲区溢出", "代码注入"],
                        "confidence": 0.9,
                        "reasoning": "dangerous_sink函数名暗示其处理危险数据"
                    }
                ]
            }
            ```'''
        
        elif "漏洞" in prompt or "vulnerability" in prompt.lower():
            return '''```json
            {
                "is_vulnerable": true,
                "vulnerability_type": "缓冲区溢出",
                "severity": "高",
                "confidence": 0.85,
                "attack_vector": "攻击者可通过input()函数输入恶意数据",
                "impact": "可能导致程序崩溃或任意代码执行",
                "remediation": "在dangerous_sink中添加输入验证和边界检查",
                "cwe_ids": ["CWE-120", "CWE-787"],
                "reasoning": "不受信任的用户输入直接传递给危险函数，缺乏适当验证"
            }
            ```'''
        
        else:
            return "这是一个智能分析的结果"

class IntelligentVulnerabilityAnalyzer:
    """集成LLM的智能漏洞分析器"""
    
    def __init__(self, src_path: str, llm_client=None):
        """
        初始化分析器
        
        :param src_path: 源代码路径
        :param llm_client: LLM客户端，如果为None则使用模拟客户端
        """
        self.src_path = src_path
        self.llm_client = llm_client or MockLLMForIntegration()
        
        # 初始化组件
        self.cpg = None
        self.llm_analyzer = None
        self.semantics = None
        self.sources = []
        self.sinks = []
        
        logger.info(f"智能漏洞分析器初始化 - 目标: {src_path}")
    
    def initialize_analysis_environment(self):
        """初始化分析环境"""
        logger.info("步骤1: 初始化分析环境...")
        
        # 创建CPG
        self.cpg = CPG(self.src_path)
        logger.info(f"✓ CPG创建完成，共发现 {len(self.cpg.functions)} 个函数")
        logger.info(f"  - 内部函数: {len(self.cpg.internal_functions)}")
        logger.info(f"  - 外部函数: {len(self.cpg.external_functions)}")
        logger.info(f"  - 操作符函数: {len(self.cpg.operator_functions)}")
        
        # 创建LLM分析器
        self.llm_analyzer = VulnerabilityLLMBridge(self.llm_client)
        logger.info("✓ LLM分析器初始化完成")
        
        # 打印外部函数信息
        logger.info("发现的外部函数:")
        for func in self.cpg.external_functions:
            logger.info(f"  - {func.full_name}")
    
    def generate_intelligent_semantics(self):
        """使用LLM生成智能语义规则"""
        logger.info("步骤2: 使用LLM生成语义规则...")
        
        # 过滤出真正的外部函数（排除操作符）
        real_external_funcs = [
            func for func in self.cpg.external_functions 
            if not func.full_name.startswith("<operator>")
        ]
        
        if real_external_funcs:
            logger.info(f"分析 {len(real_external_funcs)} 个外部函数:")
            for func in real_external_funcs:
                logger.info(f"  - {func.full_name}")
            
            # 使用LLM分析生成语义规则
            self.semantics = self.llm_analyzer.analyze_external_functions(real_external_funcs)
            logger.info(f"✓ 生成了 {len(self.semantics.rules)} 条语义规则")
            
            for i, rule in enumerate(self.semantics.rules, 1):
                logger.info(f"  规则{i}: {rule.method_full_name} -> {rule.param_flows}")
        else:
            logger.info("未发现需要分析的外部函数，使用默认语义规则")
            self.semantics = Semantics.create_default()
        
        # 手动添加一些通用规则
        self.semantics.add_memory_operation_rules()
        self.semantics.add_string_operation_rules()
        
        logger.info(f"✓ 最终共有 {len(self.semantics.rules)} 条语义规则")
    
    def identify_sources_and_sinks_intelligently(self):
        """使用LLM智能识别源和汇聚点"""
        logger.info("步骤3: 智能识别源和汇聚点...")
        
        # 使用LLM分析内部函数
        self.sources, self.sinks = self.llm_analyzer.identify_sources_and_sinks(
            self.cpg.internal_functions
        )
        
        logger.info(f"✓ 智能识别结果:")
        logger.info(f"  - 数据源: {len(self.sources)} 个")
        for source in self.sources:
            logger.info(f"    * {source.name} (参数索引: {source.index})")
        
        logger.info(f"  - 汇聚点: {len(self.sinks)} 个")
        for sink in self.sinks:
            logger.info(f"    * {sink.name} (参数索引: {sink.index})")
    
    def execute_dataflow_analysis(self):
        """执行数据流分析"""
        logger.info("步骤4: 执行数据流分析...")
        
        # 应用语义规则并执行数据流分析
        try:
            self.cpg.apply_semantics(self.semantics)
            logger.info("✓ 数据流分析完成")
        except Exception as e:
            logger.warning(f"数据流分析遇到问题: {e}")
    
    def perform_taint_analysis(self):
        """执行污点分析"""
        logger.info("步骤5: 执行污点分析...")
        
        if not self.sources or not self.sinks:
            logger.warning("缺少源或汇聚点，跳过污点分析")
            return
        
        # 执行源到汇聚的污点分析
        for source in self.sources[:3]:  # 限制分析数量
            for sink in self.sinks[:3]:
                logger.info(f"分析路径: {source.name} -> {sink.name}")
                
                try:
                    result = self.cpg.taint_analysis(source, sink)
                    if result:
                        logger.info(f"✓ 发现数据流路径")
                        # 这里可以进一步使用LLM分析路径的安全性
                    else:
                        logger.info("✗ 未发现数据流路径")
                except Exception as e:
                    logger.warning(f"污点分析失败: {e}")
    
    def generate_analysis_report(self):
        """生成智能分析报告"""
        logger.info("步骤6: 生成智能分析报告...")
        
        analysis_results = {
            "project_path": self.src_path,
            "total_functions": len(self.cpg.functions),
            "internal_functions": len(self.cpg.internal_functions),
            "external_functions": len(self.cpg.external_functions),
            "semantic_rules_generated": len(self.semantics.rules),
            "sources_identified": len(self.sources),
            "sinks_identified": len(self.sinks),
            "analysis_summary": {
                "llm_enhanced": True,
                "semantic_rules_auto_generated": len(self.semantics.rules) > 0,
                "intelligent_source_sink_detection": len(self.sources) > 0 or len(self.sinks) > 0
            }
        }
        
        # 使用LLM生成报告
        report = self.llm_analyzer.generate_security_report(analysis_results)
        
        logger.info("=" * 60)
        logger.info("智能分析报告")
        logger.info("=" * 60)
        logger.info(report)
        logger.info("=" * 60)
        
        return report
    
    def run_complete_analysis(self):
        """运行完整的智能分析流程"""
        logger.info("开始智能漏洞检测分析...")
        logger.info("=" * 60)
        
        try:
            # 执行分析流程
            self.initialize_analysis_environment()
            self.generate_intelligent_semantics()
            self.identify_sources_and_sinks_intelligently()
            self.execute_dataflow_analysis()
            self.perform_taint_analysis()
            report = self.generate_analysis_report()
            
            logger.info("✓ 智能分析完成!")
            return report
            
        except Exception as e:
            logger.error(f"分析过程中出现错误: {e}")
            raise

def main():
    """主函数"""
    # 测试路径
    test_src = "/home/nstl/data/vuln_hunter/py2joern/test/test_case/test1"
    
    print("智能漏洞检测系统")
    print("=" * 60)
    print(f"分析目标: {test_src}")
    print("=" * 60)
    
    try:
        # 创建分析器并运行
        analyzer = IntelligentVulnerabilityAnalyzer(test_src)
        report = analyzer.run_complete_analysis()
        
        print("\n" + "=" * 60)
        print("分析完成! 🎉")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n用户中断分析")
    except Exception as e:
        logger.error(f"分析失败: {e}")
        print(f"分析失败: {e}")

def test_with_real_llm():
    """测试真实LLM客户端"""
    print("\n测试真实LLM客户端连接...")
    
    try:
        # 尝试创建OpenAI客户端
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            max_tokens=1024,
            temperature=0.1
        )
        
        llm_client = create_llm_client(config)
        
        # 创建分析器
        test_src = "/home/nstl/data/vuln_hunter/py2joern/test/test_case/test1"
        analyzer = IntelligentVulnerabilityAnalyzer(test_src, llm_client)
        
        print("✓ 真实LLM客户端连接成功")
        
        # 可以在这里运行真实分析
        # analyzer.run_complete_analysis()
        
    except Exception as e:
        print(f"真实LLM客户端测试失败: {e}")
        print("回退到模拟客户端进行演示")

if __name__ == "__main__":
    # 运行主要演示
    main()
    
    # 可选: 测试真实LLM客户端
    # test_with_real_llm()
