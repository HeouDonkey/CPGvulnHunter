import unittest
import os
import time
import tempfile
import shutil
from pathlib import Path
import sys
import argparse

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from CPGvulnHunter.bridges.joernBridge import JoernBridge


class TestJoernBridge(unittest.TestCase):
    """JoernBridge 真实环境集成测试"""
    
    # 类变量用于存储 Joern 路径
    joern_path = None
    joern_available = False
    

    @classmethod
    def set_joern_path(cls, path: str):
        """设置 Joern 路径"""
        cls.joern_path = path
    
    def setUp(self):
        """每个测试前的设置"""
        if not self.joern_available:
            self.skipTest("Joern 不可用，跳过测试")
        
        self.bridge = None
        self.test_timeout = 30  # 测试超时时间
    
    def tearDown(self):
        """每个测试后的清理"""
        if self.bridge:
            try:
                self.bridge.close_shell()
            except:
                pass
    
    def test_joern_bridge_initialization(self):
        """测试 JoernBridge 初始化"""
        print(f"\n🧪 测试 JoernBridge 初始化 (使用: {self.joern_path})...")
        
        # 使用指定的 Joern 路径初始化
        self.bridge = JoernBridge(joern_path=self.joern_path, timeout=self.test_timeout)
        self.assertIsNotNone(self.bridge)
        self.assertTrue(self.bridge._is_connected())
        
        # 测试状态获取
        status = self.bridge.get_status()
        self.assertTrue(status['connected'])
        self.assertIn('joern_path', status)
        self.assertEqual(status['joern_path'], self.joern_path)
        self.assertIn('timeout', status)
        
        print("✅ 初始化测试通过")

    def test_context_manager(self):
        """测试上下文管理器"""
        print("\n🧪 测试上下文管理器...")
        
        with JoernBridge(joern_path=self.joern_path, timeout=self.test_timeout) as bridge:
            self.assertTrue(bridge._is_connected())
            status = bridge.get_status()
            self.assertTrue(status['connected'])
            self.assertEqual(status['joern_path'], self.joern_path)
        
        print("✅ 上下文管理器测试通过")

    def test_basic_commands(self):
        """测试基本命令执行"""
        print("\n🧪 测试基本命令执行...")
        
        self.bridge = JoernBridge(joern_path=self.joern_path, timeout=self.test_timeout)
        
        # 测试简单数学运算
        result = self.bridge.send_command("1 + 1")
        self.assertIn("2", result)
        print(f"  ✓ 数学运算: 1 + 1 = {result.strip()}")
        
        # 测试字符串操作
        result = self.bridge.send_command('"hello " + "world"')
        self.assertIn("hello world", result)
        print(f"  ✓ 字符串操作: {result.strip()}")
        
        # 测试列表操作
        result = self.bridge.send_command("List(1, 2, 3).size")
        self.assertIn("3", result)
        print(f"  ✓ 列表操作: {result.strip()}")
        
        print("✅ 基本命令测试通过")

    def test_health_check(self):
        """测试健康检查"""
        print("\n🧪 测试健康检查...")
        
        self.bridge = JoernBridge(joern_path=self.joern_path, timeout=self.test_timeout)
        
        # 测试健康检查
        is_healthy = self.bridge.health_check()
        self.assertTrue(is_healthy)
        print("  ✓ 健康检查通过")
        
        print("✅ 健康检查测试通过")

    def test_cpg_basic_operations(self):
        """测试 CPG 基本操作"""
        print("\n🧪 测试 CPG 基本操作...")
        
        self.bridge = JoernBridge(joern_path=self.joern_path, timeout=self.test_timeout)
        
        # 创建临时 C 源文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write("""
int add(int a, int b) {
    return a + b;
}

int main() {
    int result = add(1, 2);
    return result;
}
""")
            temp_c_file = f.name
        
        try:
            # 导入代码
            import_cmd = f'importCode("{temp_c_file}")'
            result = self.bridge.send_command(import_cmd)
            print(f"  ✓ 导入代码: {len(result)} 字符的输出")
            
            # 等待导入完成
            time.sleep(2)
            
            # 获取方法数量
            result = self.bridge.send_command("cpg.method.size")
            print(f"  ✓ 方法数量: {result.strip()}")
            
            # 获取方法名
            result = self.bridge.send_command("cpg.method.name.l")
            print(f"  ✓ 方法名: {result.strip()}")
            self.assertTrue(any(name in result for name in ["add", "main"]))
            
            print("✅ CPG 基本操作测试通过")
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_c_file)
            except:
                pass

    def test_json_output(self):
        """测试 JSON 输出格式"""
        print("\n🧪 测试 JSON 输出...")
        
        self.bridge = JoernBridge(joern_path=self.joern_path, timeout=self.test_timeout)
        
        # 创建简单的测试数据
        result = self.bridge.send_command('List("hello", "world").toJsonPretty')
        print(f"  ✓ JSON 输出: {result.strip()}")
        
        # 验证包含 JSON 标记
        self.assertTrue('"""' in result or '[' in result)
        
        print("✅ JSON 输出测试通过")

    def test_error_handling(self):
        """测试错误处理"""
        print("\n🧪 测试错误处理...")
        
        self.bridge = JoernBridge(joern_path=self.joern_path, timeout=self.test_timeout)
        
        # 测试语法错误命令
        try:
            result = self.bridge.send_command("invalid scala syntax !!!")
            # Joern 可能返回错误信息而不是抛出异常
            print(f"  ✓ 错误命令结果: {result[:100]}...")
        except Exception as e:
            print(f"  ✓ 捕获异常: {e}")
        
        # 测试连接仍然有效
        result = self.bridge.send_command("1 + 1")
        self.assertIn("2", result)
        print("  ✓ 错误后连接仍然有效")
        
        print("✅ 错误处理测试通过")

    def test_reconnection(self):
        """测试重连机制"""
        print("\n🧪 测试重连机制...")
        
        self.bridge = JoernBridge(joern_path=self.joern_path, timeout=self.test_timeout)
        
        # 验证初始连接
        self.assertTrue(self.bridge._is_connected())
        print("  ✓ 初始连接正常")
        
        # 手动关闭连接
        self.bridge._cleanup_connection()
        self.assertFalse(self.bridge._is_connected())
        print("  ✓ 连接已关闭")
        
        # 发送命令应该触发重连
        result = self.bridge.send_command("1 + 1")
        self.assertIn("2", result)
        self.assertTrue(self.bridge._is_connected())
        print("  ✓ 自动重连成功")
        
        print("✅ 重连机制测试通过")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='JoernBridge 集成测试',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认的 joern 命令
  python joernBridgeTest.py
  
  # 指定 Joern 绝对路径
  python joernBridgeTest.py --joern-path /opt/joern/joern
  
  # 使用环境变量指定路径
  JOERN_PATH=/opt/joern/joern python joernBridgeTest.py
  
  # 运行特定测试
  python joernBridgeTest.py --joern-path /opt/joern/joern TestJoernBridge.test_basic_commands
        """
    )
    
    parser.add_argument(
        '--joern-path', '-p',
        type=str,
        help='Joern 可执行文件的路径 (默认: joern)',
        default=None
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        help='命令超时时间（秒）(默认: 30)',
        default=30
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示更详细的输出'
    )
    
    return parser.parse_known_args()


def run_integration_test(joern_path=None):
    """运行集成测试的便捷函数"""
    print("🚀 开始 JoernBridge 集成测试")
    print("=" * 50)
    
    # 设置 Joern 路径
    if joern_path:
        TestJoernBridge.set_joern_path(joern_path)
        print(f"📍 使用指定的 Joern 路径: {joern_path}")
    
    # 检查环境
    test_joern_path = TestJoernBridge.joern_path or os.getenv('JOERN_PATH', 'joern')
    
    if os.path.isabs(test_joern_path):
        if not os.path.isfile(test_joern_path):
            print(f"❌ 错误: 指定的 Joern 路径不存在: {test_joern_path}")
            return False
    else:
        if not shutil.which(test_joern_path):
            print(f"❌ 错误: 未找到 joern 命令: {test_joern_path}")
            print("请确保:")
            print("1. Joern 已正确安装")
            print("2. 使用 --joern-path 参数指定正确的路径")
            print("3. 或设置 JOERN_PATH 环境变量")
            return False
    
    # 运行测试
    unittest.main(argv=[''], verbosity=2, exit=False)
    return True


if __name__ == '__main__':
    # 解析命令行参数
    args, remaining_args = parse_arguments()
    
    # 设置环境变量以显示更多信息
    os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
    
    print("JoernBridge 真实环境测试")
    
    if args.joern_path:
        print(f"使用指定的 Joern 路径: {args.joern_path}")
    elif os.getenv('JOERN_PATH'):
        print(f"使用环境变量 JOERN_PATH: {os.getenv('JOERN_PATH')}")
    else:
        print("使用默认的 joern 命令")
    
    print()
    
    # 运行测试
    success = run_integration_test(args.joern_path)
    
    if not success:
        sys.exit(1)