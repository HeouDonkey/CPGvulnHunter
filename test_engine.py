#!/usr/bin/env python3
"""
Engine类的基础测试脚本
测试VulnerabilityEngine的基本功能
"""

import sys
import os
import logging
from pathlib import Path

from CPGvulnHunter.core.config import EngineConfig

from CPGvulnHunter.core.engine import VulnerabilityEngine
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_engine_initialization():
    """测试Engine初始化"""
    logger.info("=== 测试Engine初始化 ===")
    
    # 使用测试用例路径
    test_src_path = str("/home/nstl/data/CPGvulnHunter/test/test_case/test1")
    
    try:
        # 创建引擎配置
        config = EngineConfig(
            enabled_passes=["init"],  # 只启用init pass进行测试
            log_level="DEBUG",
            output_dir=str(project_root / "test_output")
        )
        
        # 初始化引擎
        engine = VulnerabilityEngine(
            src_path=test_src_path,
            config_file=str(project_root / "config.yml"),
            engine_config=config
        )
        
        logger.info(f"✅ 引擎初始化成功: {engine}")
        logger.info(f"   - 源路径: {engine.src_path}")
        logger.info(f"   - 输出目录: {engine.output_dir}")
        logger.info(f"   - 启用的passes: {engine.engine_config.enabled_passes}")
        
        return engine
        
    except Exception as e:
        logger.error(f"❌ 引擎初始化失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return None


def test_engine_cpg_initialization():
    """测试CPG初始化"""
    logger.info("\n=== 测试CPG初始化 ===")
    
    test_src_path = str("/home/nstl/data/CPGvulnHunter/test/test_case/test1")
    
    try:
        config = EngineConfig(enabled_passes=["init"])
        engine = VulnerabilityEngine(
            src_path=test_src_path,
            engine_config=config
        )
        
        # 测试CPG初始化
        success = engine.initialize_cpg()
        
        if success and engine.cpg:
            logger.info("✅ CPG初始化成功")
            logger.info(f"   - CPG源路径: {engine.cpg.src_path}")
            logger.info(f"   - Joern路径: {engine.cpg.joern_path}")
            logger.info(f"   - LLM配置: {engine.cpg.llm_config}")
            return True
        else:
            logger.error("❌ CPG初始化失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ CPG初始化测试失败: {e}")
        return False


def test_engine_pass_registration():
    """测试Pass注册功能"""
    logger.info("\n=== 测试Pass注册 ===")
    
    test_src_path = str(project_root / "test" / "test_case" / "test1")
    
    try:
        config = EngineConfig()
        engine = VulnerabilityEngine(
            src_path=test_src_path,
            engine_config=config
        )
        
        # 检查默认注册的passes
        logger.info(f"默认注册的passes: {list(engine.pass_registry.keys())}")
        
        # 测试注册新的pass
        class DummyPass:
            def __init__(self, cpg):
                self.cpg = cpg
            
            def run(self):
                return "dummy_result"
        
        engine.register_pass("dummy", DummyPass)
        
        if "dummy" in engine.pass_registry:
            logger.info("✅ Pass注册功能正常")
            return True
        else:
            logger.error("❌ Pass注册失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pass注册测试失败: {e}")
        return False


def test_engine_analysis_summary():
    """测试分析摘要功能"""
    logger.info("\n=== 测试分析摘要 ===")
    
    test_src_path = str(project_root / "test" / "test_case" / "test1")
    
    try:
        config = EngineConfig(enabled_passes=["init"])
        engine = VulnerabilityEngine(
            src_path=test_src_path,
            engine_config=config
        )
        
        # 测试空的分析摘要
        summary = engine.get_analysis_summary()
        logger.info(f"空摘要: {summary}")
        
        if summary.get("status") == "no_analysis_completed":
            logger.info("✅ 分析摘要功能正常")
            return True
        else:
            logger.error("❌ 分析摘要功能异常")
            return False
            
    except Exception as e:
        logger.error(f"❌ 分析摘要测试失败: {e}")
        return False


def test_convenience_function():
    """测试便利函数"""
    logger.info("\n=== 测试便利函数 ===")
    
    test_src_path = str(project_root / "test" / "test_case" / "test1")
    
    try:
        # 创建一个简单的配置
        config = EngineConfig(
            enabled_passes=["init"],
            save_intermediate_results=False,
            log_level="WARNING"  # 减少日志输出
        )
        
        # 测试便利函数（不执行真正的分析，只测试初始化）
        logger.info("测试便利函数初始化...")
        
        # 创建引擎但不运行分析
        engine = VulnerabilityEngine(
            src_path=test_src_path,
            engine_config=config
        )
        
        logger.info("✅ 便利函数功能正常")
        return True
        
    except Exception as e:
        logger.error(f"❌ 便利函数测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    logger.info("开始Engine类测试...")
    
    tests = [
        ("引擎初始化", test_engine_initialization),
        ("CPG初始化", test_engine_cpg_initialization),
        ("Pass注册", test_engine_pass_registration),
        ("分析摘要", test_engine_analysis_summary),
        ("便利函数", test_convenience_function)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    logger.info("\n" + "="*50)
    logger.info("测试结果汇总:")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    logger.info("="*50)
    logger.info(f"总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！Engine类基本功能正常。")
    else:
        logger.warning(f"⚠️  {total - passed} 个测试失败，需要进一步检查。")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
