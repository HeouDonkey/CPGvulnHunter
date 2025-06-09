#!/usr/bin/env python3
"""
测试统一配置系统
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


from CPGvulnHunter.core.config import UnifiedConfig
from CPGvulnHunter.core.engine import VulnerabilityEngine
from CPGvulnHunter.core.cpg import CPG

def test_config_loading():
    """测试配置加载"""
    print("=" * 50)
    print("测试统一配置系统")
    print("=" * 50)
    
    # 测试从文件加载配置
    config_file = project_root / "config.yml"
    if not config_file.exists():
        print(f"配置文件不存在: {config_file}")
        return False
    
    try:
        config = UnifiedConfig.from_file(str(config_file))
        print("✓ 配置加载成功")
        
        # 显示配置内容
        print("\n配置内容:")
        print(f"项目名称: {config.project_name}")
        print(f"版本: {config.version}")
        print(f"调试模式: {config.debug_mode}")
        
        print(f"\nLLM配置:")
        print(f"  基础URL: {config.llm.base_url}")
        print(f"  模型: {config.llm.model}")
        print(f"  温度: {config.llm.temperature}")
        
        print(f"\nJoern配置:")
        print(f"  安装路径: {config.joern.installation_path}")
        print(f"  超时时间: {config.joern.timeout}")
        print(f"  内存限制: {config.joern.memory_limit}")
        
        print(f"\nEngine配置:")
        print(f"  最大调用深度: {config.engine.max_call_depth}")
        print(f"  启用的Pass: {config.engine.enabled_passes}")
        
        print(f"\n日志配置:")
        print(f"  日志级别: {config.logging.level}")
        print(f"  日志格式: {config.logging.format}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False

def test_config_validation():
    """测试配置验证"""
    print("\n" + "=" * 50)
    print("测试配置验证")
    print("=" * 50)
    
    try:
        config = UnifiedConfig.from_file(str(project_root / "config.yml"))
        
        # 测试必要配置是否存在
        assert config.llm.base_url, "LLM基础URL不能为空"
        assert config.joern.installation_path, "Joern安装路径不能为空"
        assert config.engine.enabled_passes, "启用的Pass列表不能为空"
        
        print("✓ 配置验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 配置验证失败: {e}")
        return False

def test_engine_initialization():
    """测试Engine初始化"""
    print("\n" + "=" * 50)
    print("测试Engine初始化")
    print("=" * 50)
    
    try:
        config = UnifiedConfig.from_file(str(project_root / "config.yml"))
        
        # 测试从配置文件初始化Engine
        engine = VulnerabilityEngine("/tmp/test_source", config_file=str(project_root / "config.yml"))
        print("✓ Engine从配置文件初始化成功")
        
        # 测试从配置对象初始化Engine
        engine2 = VulnerabilityEngine("/tmp/test_source", config=config)
        print("✓ Engine从配置对象初始化成功")
        
        # 检查Engine配置是否正确
        assert engine.config.llm.model == config.llm.model
        assert engine.config.joern.timeout == config.joern.timeout
        
        print("✓ Engine配置验证通过")
        return True
        
    except Exception as e:
        print(f"✗ Engine初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cpg_initialization():
    """测试CPG初始化"""
    print("\n" + "=" * 50)
    print("测试CPG初始化")
    print("=" * 50)
    
    try:
        config = UnifiedConfig.from_file(str(project_root / "config.yml"))
        
        # 测试CPG初始化
        # 注意：这里我们使用一个虚拟的源码路径来测试
        test_src_path = "/tmp/test_source"
        
        # 使用新的from_config方法
        cpg = CPG.from_config(test_src_path, config)
        print("✓ CPG从配置对象初始化成功")
        
        # 测试向后兼容的属性访问
        assert cpg.cpg_var == config.joern.cpg_var
        assert cpg.joern_path == config.joern.installation_path
        assert cpg.llm_config == config.llm
        
        print("✓ CPG配置属性访问正常")
        return True
        
    except Exception as e:
        print(f"✗ CPG初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试统一配置系统...")
    
    tests = [
        test_config_loading,
        test_config_validation,
        test_engine_initialization,
        test_cpg_initialization
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("测试结果")
    print("=" * 50)
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
