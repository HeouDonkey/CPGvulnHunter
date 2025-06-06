#!/usr/bin/env python3
"""
完整的LLM辅助漏洞检测示例
展示增强版LLM桥接器和高级分析器的使用
"""

import sys
import os
import logging
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from py2joern.llmBridge.enhanced_bridge import EnhancedVulnerabilityLLMBridge, create_enhanced_llm_bridge
from py2joern.llmBridge.advanced_analyzer import AdvancedVulnerabilityAnalyzer
from py2joern.cpgs.cpg import CPG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveLLMDemo:
    """全面的LLM功能演示"""
    
    def __init__(self, test_src_path: str):
        self.test_src_path = test_src_path
        self.results = {}
    
    def demo_basic_llm_functionality(self):
        """演示基础LLM功能"""
        logger.info("=== 演示基础LLM功能 ===")
        
        try:
            # 创建模拟LLM客户端
            mock_client = MockAdvancedLLMClient()
            
            # 创建基础LLM桥接器
            llm_bridge = EnhancedVulnerabilityLLMBridge(mock_client, {
                'enable_caching': False,  # 演示时禁用缓存
                'enable_rate_limiting': False
            })
            
            # 创建CPG
            cpg = CPG(self.test_src_path)
            logger.info(f"✓ CPG创建完成，发现 {len(cpg.functions)} 个函数")
            
            # 演示语义规则生成
            logger.info("\n1. 语义规则生成演示")
            external_funcs = [f for f in cpg.external_functions 
                            if not f.full_name.startswith("<operator>")]
            
            if external_funcs:
                semantics = llm_bridge.analyze_external_functions(external_funcs[:5])
                logger.info(f"✓ 生成了 {len(semantics.rules)} 条语义规则")
                
                for i, rule in enumerate(semantics.rules[:3], 1):
                    logger.info(f"  规则{i}: {rule.method_full_name} -> {rule.param_flows}")
            
            # 演示源/汇聚点识别
            logger.info("\n2. 源/汇聚点识别演示")
            internal_funcs = cpg.internal_functions[:10]  # 限制数量
            
            if internal_funcs:
                sources, sinks = llm_bridge.identify_sources_and_sinks(internal_funcs)
                logger.info(f"✓ 识别出 {len(sources)} 个源，{len(sinks)} 个汇聚点")
                
                for source in sources[:3]:
                    logger.info(f"  源: {source.name}")
                for sink in sinks[:3]:
                    logger.info(f"  汇聚点: {sink.name}")
            
            # 演示代码解释
            logger.info("\n3. 代码行为解释演示")
            sample_code = """
            char* dangerous_function(char* input) {
                char buffer[100];
                strcpy(buffer, input);  // 潜在缓冲区溢出
                return buffer;          // 返回局部变量地址
            }
            """
            
            explanation = llm_bridge.explain_code_behavior(sample_code)
            logger.info("✓ 代码解释:")
            logger.info(f"  {explanation[:200]}...")
            
            self.results['basic_demo'] = {
                'semantic_rules': len(semantics.rules) if 'semantics' in locals() else 0,
                'sources_found': len(sources) if 'sources' in locals() else 0,
                'sinks_found': len(sinks) if 'sinks' in locals() else 0,
                'code_explanation_length': len(explanation)
            }
            
        except Exception as e:
            logger.error(f"基础功能演示失败: {e}")
    
    def demo_enhanced_features(self):
        """演示增强功能"""
        logger.info("\n=== 演示增强功能 ===")
        
        try:
            # 创建增强版LLM桥接器
            enhanced_bridge = create_enhanced_llm_bridge("mock", {
                'enable_caching': True,
                'enable_rate_limiting': True,
                'cache_size': 100,
                'rate_limit': 10
            })
            
            # 替换为模拟客户端
            enhanced_bridge.llm_client = MockAdvancedLLMClient()
            
            logger.info("✓ 增强版LLM桥接器创建成功")
            
            # 演示缓存功能
            logger.info("\n1. 缓存功能演示")
            cpg = CPG(self.test_src_path)
            
            # 第一次请求（会缓存）
            start_time = logger.info("第一次分析...")
            semantics1 = enhanced_bridge.analyze_external_functions(cpg.external_functions[:3])
            
            # 第二次相同请求（使用缓存）
            logger.info("第二次分析（应该使用缓存）...")
            semantics2 = enhanced_bridge.analyze_external_functions(cpg.external_functions[:3])
            
            # 获取性能统计
            stats = enhanced_bridge.get_performance_stats()
            logger.info(f"✓ 缓存统计: {stats}")
            
            # 演示批处理功能
            logger.info("\n2. 批处理功能演示")
            from py2joern.llmBridge.llmBridge import AnalysisType
            
            batch_results = enhanced_bridge.analyze_functions_batch(
                cpg.external_functions[:6], 
                AnalysisType.SEMANTIC_RULES,
                batch_size=3
            )
            
            logger.info(f"✓ 批处理完成，处理了 {len(batch_results)} 个批次")
            
            self.results['enhanced_demo'] = {
                'cache_stats': stats,
                'batch_count': len(batch_results)
            }
            
        except Exception as e:
            logger.error(f"增强功能演示失败: {e}")
    
    def demo_advanced_analyzer(self):
        """演示高级分析器"""
        logger.info("\n=== 演示高级分析器 ===")
        
        try:
            # 创建高级分析器
            analyzer = AdvancedVulnerabilityAnalyzer(
                project_path=self.test_src_path,
                workspace_dir="./demo_workspace",
                llm_provider="mock"
            )
            
            # 替换为模拟客户端
            analyzer.llm_bridge.llm_client = MockAdvancedLLMClient()
            
            logger.info("✓ 高级分析器创建成功")
            
            # 演示增量分析
            logger.info("\n1. 增量分析演示")
            
            # 第一次全量分析
            logger.info("执行第一次全量分析...")
            results1 = analyzer.incremental_analysis(force_full_analysis=True)
            logger.info(f"✓ 第一次分析完成: {results1['status']}")
            
            # 第二次增量分析（无变更）
            logger.info("执行第二次增量分析...")
            results2 = analyzer.incremental_analysis(force_full_analysis=False)
            logger.info(f"✓ 第二次分析完成: {results2['status']}")
            
            # 获取仪表板数据
            logger.info("\n2. 分析仪表板演示")
            dashboard = analyzer.get_analysis_dashboard()
            
            logger.info("✓ 分析摘要:")
            logger.info(f"  - 总会话数: {dashboard['summary']['total_sessions']}")
            logger.info(f"  - 发现漏洞数: {dashboard['summary']['total_vulnerabilities']}")
            logger.info(f"  - 工作目录: {dashboard['summary']['workspace_dir']}")
            
            # 导出结果
            logger.info("\n3. 结果导出演示")
            export_file = analyzer.export_results("json")
            logger.info(f"✓ 结果已导出到: {export_file}")
            
            self.results['advanced_demo'] = {
                'first_analysis': results1['status'],
                'second_analysis': results2['status'],
                'dashboard_summary': dashboard['summary'],
                'export_file': export_file
            }
            
        except Exception as e:
            logger.error(f"高级分析器演示失败: {e}")
    
    def demo_integration_workflow(self):
        """演示完整集成工作流"""
        logger.info("\n=== 演示完整集成工作流 ===")
        
        try:
            # 创建完整的分析工作流
            logger.info("1. 初始化完整分析环境...")
            
            # 高级分析器
            analyzer = AdvancedVulnerabilityAnalyzer(
                project_path=self.test_src_path,
                workspace_dir="./integration_workspace"
            )
            analyzer.llm_bridge.llm_client = MockAdvancedLLMClient()
            
            # 执行完整分析
            logger.info("2. 执行完整安全分析...")
            analysis_results = analyzer.incremental_analysis(force_full_analysis=True)
            
            if analysis_results['status'] == 'success':
                logger.info("✓ 安全分析完成")
                
                # 获取详细结果
                results = analysis_results['results']
                logger.info(f"  - 分析的函数数量: {analysis_results['functions_analyzed']}")
                logger.info(f"  - 生成的语义规则: {len(results['semantics'].rules) if results['semantics'] else 0}")
                logger.info(f"  - 识别的源: {len(results['sources'])}")
                logger.info(f"  - 识别的汇聚点: {len(results['sinks'])}")
                logger.info(f"  - 发现的漏洞: {len(results['vulnerabilities'])}")
                
                # 生成最终报告
                logger.info("3. 生成综合安全报告...")
                report = analysis_results.get('report', '')
                logger.info(f"✓ 安全报告生成完成 ({len(report)} 字符)")
                
                # 保存演示结果
                demo_report_file = "./integration_demo_report.md"
                with open(demo_report_file, 'w', encoding='utf-8') as f:
                    f.write("# LLM辅助漏洞检测演示报告\n\n")
                    f.write(f"## 分析概览\n")
                    f.write(f"- 项目路径: {self.test_src_path}\n")
                    f.write(f"- 分析状态: {analysis_results['status']}\n")
                    f.write(f"- 会话ID: {analysis_results['session_id']}\n\n")
                    f.write(f"## 详细报告\n{report}\n")
                
                logger.info(f"✓ 演示报告已保存到: {demo_report_file}")
                
                self.results['integration_demo'] = {
                    'analysis_status': analysis_results['status'],
                    'functions_analyzed': analysis_results['functions_analyzed'],
                    'report_file': demo_report_file,
                    'report_length': len(report)
                }
            
        except Exception as e:
            logger.error(f"集成工作流演示失败: {e}")
    
    def generate_demo_summary(self):
        """生成演示摘要"""
        logger.info("\n=== 演示摘要 ===")
        
        logger.info("📊 演示结果汇总:")
        
        for demo_name, results in self.results.items():
            logger.info(f"\n{demo_name.upper()}:")
            for key, value in results.items():
                logger.info(f"  - {key}: {value}")
        
        # 保存完整的演示结果
        import json
        summary_file = "./llm_demo_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✓ 完整演示结果已保存到: {summary_file}")
        
        logger.info(f"\n🎉 LLM辅助漏洞检测功能演示完成！")
        logger.info("主要功能包括:")
        logger.info("  1. ✅ 智能语义规则生成")
        logger.info("  2. ✅ 自动源/汇聚点识别")
        logger.info("  3. ✅ 代码行为智能解释")
        logger.info("  4. ✅ 增强缓存和批处理")
        logger.info("  5. ✅ 增量分析和结果持久化")
        logger.info("  6. ✅ 综合安全报告生成")


class MockAdvancedLLMClient:
    """高级模拟LLM客户端"""
    
    def __init__(self):
        self.request_count = 0
    
    def generate(self, prompt: str, **kwargs) -> str:
        """模拟LLM响应生成"""
        self.request_count += 1
        
        if "语义规则" in prompt or "semantic" in prompt.lower():
            return self._generate_semantic_rules()
        elif "源" in prompt and "汇聚" in prompt:
            return self._generate_sources_sinks()
        elif "漏洞" in prompt or "vulnerability" in prompt.lower():
            return self._generate_vulnerability_analysis()
        elif "解释" in prompt or "explain" in prompt.lower():
            return self._generate_code_explanation()
        elif "报告" in prompt or "report" in prompt.lower():
            return self._generate_security_report()
        else:
            return "模拟LLM响应：分析完成"
    
    def _generate_semantic_rules(self) -> str:
        return '''```json
        {
            "semantic_rules": [
                {
                    "method_pattern": "^.*strcpy$",
                    "param_flows": [[1, 0]],
                    "is_regex": true,
                    "confidence": 0.95,
                    "reasoning": "strcpy函数将源字符串复制到目标缓冲区"
                },
                {
                    "method_pattern": "^.*malloc$",
                    "param_flows": [[-1, -1]],
                    "is_regex": true,
                    "confidence": 0.9,
                    "reasoning": "malloc返回分配的内存地址"
                }
            ]
        }
        ```'''
    
    def _generate_sources_sinks(self) -> str:
        return '''```json
        {
            "sources": [
                {
                    "function_name": "input",
                    "parameter_index": -1,
                    "source_type": "用户输入",
                    "confidence": 0.9,
                    "reasoning": "input函数获取用户输入数据"
                }
            ],
            "sinks": [
                {
                    "function_name": "dangerous_sink",
                    "parameter_index": 1,
                    "sink_type": "危险处理",
                    "vulnerability_types": ["缓冲区溢出"],
                    "confidence": 0.85,
                    "reasoning": "dangerous_sink函数处理可能不安全的数据"
                }
            ]
        }
        ```'''
    
    def _generate_vulnerability_analysis(self) -> str:
        return '''```json
        {
            "is_vulnerable": true,
            "vulnerability_type": "缓冲区溢出",
            "severity": "高",
            "confidence": 0.88,
            "attack_vector": "攻击者通过输入超长字符串触发缓冲区溢出",
            "impact": "可能导致程序崩溃或任意代码执行",
            "remediation": "使用安全的字符串操作函数，如strncpy，并进行边界检查",
            "cwe_ids": ["CWE-120", "CWE-787"],
            "reasoning": "数据从不受信任的输入源流向了缺乏边界检查的字符串操作函数"
        }
        ```'''
    
    def _generate_code_explanation(self) -> str:
        return """
        ## 代码行为分析
        
        ### 主要功能
        这个函数接收一个字符串输入，并将其复制到一个固定大小的缓冲区中。
        
        ### 潜在安全风险
        1. **缓冲区溢出**: strcpy不检查目标缓冲区大小，可能导致溢出
        2. **返回局部变量**: 函数返回局部数组的地址，是未定义行为
        
        ### 建议改进
        1. 使用strncpy替代strcpy
        2. 返回动态分配的内存或使用调用者提供的缓冲区
        3. 添加输入长度验证
        """
    
    def _generate_security_report(self) -> str:
        return """
        # 安全分析报告
        
        ## 执行摘要
        本次分析共检测了多个函数，发现了若干潜在的安全风险。通过LLM辅助分析，
        系统能够智能识别源/汇聚点并生成相应的语义规则。
        
        ## 发现的漏洞
        - 缓冲区溢出风险: 1个
        - 不安全的字符串操作: 2个
        
        ## 风险等级评估
        整体风险等级: 中等
        
        ## 修复建议
        1. 使用安全的字符串操作函数
        2. 添加输入验证和边界检查
        3. 考虑使用更安全的内存管理方式
        
        ## 技术细节
        分析使用了先进的LLM技术，结合静态代码分析工具Joern，
        提供了智能化的漏洞检测能力。
        """


def main():
    """主演示函数"""
    # 设置测试代码路径
    test_src_path = "/home/nstl/data/vuln_hunter/py2joern/test/test_case/test1"
    
    # 检查测试路径是否存在
    if not os.path.exists(test_src_path):
        logger.warning(f"测试路径不存在: {test_src_path}")
        logger.info("使用当前目录作为测试路径")
        test_src_path = os.getcwd()
    
    # 创建演示实例
    demo = ComprehensiveLLMDemo(test_src_path)
    
    logger.info("🚀 开始LLM辅助漏洞检测功能演示")
    logger.info(f"测试项目路径: {test_src_path}")
    
    # 执行各种演示
    demo.demo_basic_llm_functionality()
    demo.demo_enhanced_features() 
    demo.demo_advanced_analyzer()
    demo.demo_integration_workflow()
    
    # 生成总结
    demo.generate_demo_summary()


if __name__ == "__main__":
    main()
