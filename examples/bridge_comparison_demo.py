#!/usr/bin/env python3
"""
LLM Bridge 使用示例对比
演示基础版和增强版的使用差异
"""

import time
from typing import List
from py2joern.llmBridge.config import create_mock_client
from py2joern.llmBridge.llmBridge import VulnerabilityLLMBridge
from py2joern.llmBridge.enhanced_bridge import EnhancedVulnerabilityLLMBridge
from py2joern.models.function import Function

def create_sample_functions() -> List[Function]:
    """创建示例函数用于测试"""
    functions = []
    
    # 模拟一些外部函数
    for i in range(10):
        func = Function(
            name=f"external_func_{i}",
            signature=f"def external_func_{i}(data): pass",
            ast_node=None,
            local_variables=[],
            external_calls=[],
            return_variables=[]
        )
        functions.append(func)
    
    return functions

def demo_basic_bridge():
    """演示基础版LLM Bridge的使用"""
    print("=" * 60)
    print("基础版 VulnerabilityLLMBridge 演示")
    print("=" * 60)
    
    # 创建客户端和桥接器
    client = create_mock_client()
    bridge = VulnerabilityLLMBridge(client)
    
    functions = create_sample_functions()
    
    print(f"分析 {len(functions)} 个函数...")
    
    # 记录时间
    start_time = time.time()
    
    # 1. 分析外部函数
    print("\n1. 分析外部函数...")
    semantic_results = bridge.analyze_external_functions(functions)
    print(f"   ✅ 生成了 {len(semantic_results)} 个语义规则")
    
    # 2. 识别源和汇聚点
    print("\n2. 识别源和汇聚点...")
    code_content = "def process_user_input(data): return eval(data)"
    sources_sinks = bridge.identify_sources_and_sinks(code_content)
    print(f"   ✅ 识别源: {len(sources_sinks.get('sources', []))}")
    print(f"   ✅ 识别汇聚点: {len(sources_sinks.get('sinks', []))}")
    
    # 3. 生成安全报告
    print("\n3. 生成安全报告...")
    analysis_results = {
        'semantic_rules': semantic_results,
        'sources_sinks': sources_sinks,
        'vulnerability_count': 2
    }
    report = bridge.generate_security_report(analysis_results)
    print(f"   ✅ 生成报告: {report['summary'][:50]}...")
    
    end_time = time.time()
    print(f"\n⏱️  总耗时: {end_time - start_time:.2f} 秒")
    print(f"💰 API调用次数: ~{len(functions) + 3} 次")

def demo_enhanced_bridge():
    """演示增强版LLM Bridge的使用"""
    print("\n" + "=" * 60)
    print("增强版 EnhancedVulnerabilityLLMBridge 演示")
    print("=" * 60)
    
    # 创建客户端和增强桥接器
    client = create_mock_client()
    bridge = EnhancedVulnerabilityLLMBridge(
        llm_client=client,
        cache_config={
            'max_size': 1000,
            'ttl_seconds': 3600  # 1小时缓存
        },
        rate_limit_config={
            'calls_per_minute': 60,
            'burst_size': 10
        }
    )
    
    functions = create_sample_functions()
    
    print(f"分析 {len(functions)} 个函数...")
    
    # 记录时间
    start_time = time.time()
    
    # 1. 带上下文跟踪的分析
    print("\n1. 上下文感知分析...")
    context_results = bridge.analyze_with_context_tracking(functions)
    print(f"   ✅ 分析了 {len(context_results)} 个函数的上下文关系")
    
    # 2. 批量识别源和汇聚点
    print("\n2. 批量源汇聚点识别...")
    code_samples = [
        "def process_user_input(data): return eval(data)",
        "def execute_command(cmd): os.system(cmd)",
        "def read_file(path): open(path).read()"
    ]
    
    # 使用批处理功能
    batch_results = []
    for code in code_samples:
        result = bridge.identify_sources_and_sinks(code)
        batch_results.append(result)
    
    print(f"   ✅ 批量处理了 {len(batch_results)} 个代码片段")
    
    # 3. 性能统计
    print("\n3. 性能统计...")
    stats = bridge.get_performance_stats()
    print(f"   📊 缓存命中率: {stats['cache_hit_rate']:.1%}")
    print(f"   📊 平均响应时间: {stats['avg_response_time']:.3f}秒")
    print(f"   📊 总请求数: {stats['total_requests']}")
    print(f"   📊 缓存节省: {stats['cache_saves']} 次API调用")
    
    end_time = time.time()
    print(f"\n⏱️  总耗时: {end_time - start_time:.2f} 秒")
    
    # 4. 演示缓存效果 - 重复相同分析
    print("\n4. 演示缓存效果 - 重复分析...")
    repeat_start = time.time()
    
    # 重复相同的分析（应该从缓存获取）
    cached_results = bridge.analyze_with_context_tracking(functions[:3])
    
    repeat_end = time.time()
    print(f"   ⚡ 缓存重复分析耗时: {repeat_end - repeat_start:.3f} 秒")
    
    # 最终统计
    final_stats = bridge.get_performance_stats()
    print(f"   📈 最终缓存命中率: {final_stats['cache_hit_rate']:.1%}")

def demo_migration_compatibility():
    """演示迁移兼容性"""
    print("\n" + "=" * 60)
    print("迁移兼容性演示")
    print("=" * 60)
    
    client = create_mock_client()
    functions = create_sample_functions()[:3]  # 用少量函数演示
    
    # 使用相同的代码，不同的桥接器
    print("使用相同代码调用两个不同的桥接器:")
    
    def analyze_with_bridge(bridge, bridge_name):
        """通用分析函数"""
        print(f"\n🔄 使用 {bridge_name}:")
        start = time.time()
        
        # 相同的API调用
        semantic_results = bridge.analyze_external_functions(functions)
        code_content = "def test(): pass"
        sources_sinks = bridge.identify_sources_and_sinks(code_content)
        
        end = time.time()
        print(f"   ✅ 语义规则: {len(semantic_results)}")
        print(f"   ✅ 源汇聚点: {len(sources_sinks.get('sources', []))} | {len(sources_sinks.get('sinks', []))}")
        print(f"   ⏱️  耗时: {end - start:.3f}秒")
        
        return semantic_results, sources_sinks
    
    # 基础版
    basic_bridge = VulnerabilityLLMBridge(client)
    basic_results = analyze_with_bridge(basic_bridge, "基础版")
    
    # 增强版 - 使用相同的API
    enhanced_bridge = EnhancedVulnerabilityLLMBridge(client)
    enhanced_results = analyze_with_bridge(enhanced_bridge, "增强版")
    
    print(f"\n✅ 两个版本的API完全兼容！")
    print(f"基础版结果数量: {len(basic_results[0])}")
    print(f"增强版结果数量: {len(enhanced_results[0])}")

def demo_performance_comparison():
    """性能对比演示"""
    print("\n" + "=" * 60)
    print("性能对比演示")
    print("=" * 60)
    
    client = create_mock_client()
    functions = create_sample_functions()
    
    # 基础版性能测试
    print("🔬 基础版性能测试...")
    basic_bridge = VulnerabilityLLMBridge(client)
    
    start = time.time()
    for _ in range(3):  # 重复3次相同分析
        basic_bridge.analyze_external_functions(functions[:5])
    basic_time = time.time() - start
    print(f"   ⏱️  基础版 (3次重复): {basic_time:.3f}秒")
    
    # 增强版性能测试
    print("\n🚀 增强版性能测试...")
    enhanced_bridge = EnhancedVulnerabilityLLMBridge(client)
    
    start = time.time()
    for _ in range(3):  # 重复3次相同分析（应该命中缓存）
        enhanced_bridge.analyze_external_functions(functions[:5])
    enhanced_time = time.time() - start
    
    stats = enhanced_bridge.get_performance_stats()
    print(f"   ⏱️  增强版 (3次重复): {enhanced_time:.3f}秒")
    print(f"   📊 缓存命中率: {stats['cache_hit_rate']:.1%}")
    print(f"   💰 节省API调用: {stats['cache_saves']} 次")
    
    # 性能提升计算
    if enhanced_time > 0:
        speedup = basic_time / enhanced_time
        print(f"\n📈 性能提升: {speedup:.1f}x 倍")
        print(f"💡 时间节省: {((basic_time - enhanced_time) / basic_time * 100):.1f}%")

def main():
    """主演示函数"""
    print("🚀 LLM Bridge 功能对比演示")
    print("这个演示将展示基础版和增强版LLM桥接器的区别")
    
    # 演示基础版
    demo_basic_bridge()
    
    # 演示增强版
    demo_enhanced_bridge()
    
    # 演示迁移兼容性
    demo_migration_compatibility()
    
    # 性能对比
    demo_performance_comparison()
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print("📋 基础版适合:")
    print("   - 🎓 学习和实验")
    print("   - 🚀 快速原型开发")
    print("   - 🔍 小规模分析")
    print("")
    print("🚀 增强版适合:")
    print("   - 🏭 生产环境")
    print("   - 📊 大规模分析")
    print("   - 💰 成本控制")
    print("   - ⚡ 性能优化")
    print("")
    print("✅ 两个版本API完全兼容，可以轻松迁移！")

if __name__ == "__main__":
    main()
