from typing import Optional, List, Dict, Any, Union, Pattern
from dataclasses import dataclass
import os
import re
import json
import shutil
import logging
import time
import threading
import pexpect

class JoernBridge:
    """
    与 Joern 命令行交互的桥接类
    提供稳定的连接管理和命令执行功能
    """
    
    def __init__(self, joern_path: str = "joern", timeout: int = 120) -> None:
        self.joern_path: str = joern_path if os.path.isabs(joern_path) else shutil.which(joern_path) or joern_path
        self.timeout: int = timeout
        self._child: Optional[pexpect.spawn] = None
        self._lock: threading.Lock = threading.Lock()
        self._last_activity: float = time.time()
        
        # 编译正则表达式以提高性能
        self._ansi_escape: Pattern[str] = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self._control_chars: Pattern[str] = re.compile(r'[\r\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]+')
        self._multi_newlines: Pattern[str] = re.compile(r'\n{2,}')
        
        # 调试相关
        self._debug_mode = False
        self._command_history = []
        
        self._setup_logging()
        self.open_shell()

    def _setup_logging(self) -> None:
        """设置日志记录"""
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            # Ensure logger uses the level from config
            self.logger.setLevel(logging.getLogger().level)

    def enable_debug(self, debug_file: str = None):
        """启用调试模式"""
        self._debug_mode = True
        if debug_file:
            self._debug_file = debug_file
        else:
            self._debug_file = "/home/nstl/data/CPGvulnHunter/logs/joern_debug.log"

    def _debug_log(self, message: str):
        """写入调试日志"""
        if self._debug_mode:
            try:
                with open(self._debug_file, 'a', encoding='utf-8') as f:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] {message}\n")
            except:
                pass

    def _is_connected(self) -> bool:
        """检查连接是否有效"""
        if self._child is None:
            return False
        return self._child.isalive()

    def open_shell(self, retry_count: int = 3) -> None:
        """打开Joern shell连接"""
        with self._lock:
            if self._is_connected():
                return
                
            try:
                import pexpect
            except ImportError:
                raise ImportError("请先安装pexpect库: pip install pexpect")
            
            import shlex
            
            # 清理旧连接
            self._cleanup_connection()
            
            for attempt in range(retry_count):
                try:
                    self.logger.info(f"启动Joern shell (尝试 {attempt + 1}/{retry_count})")
                    self._debug_log(f"启动Joern: {self.joern_path}")
                    
                    # 设置环境变量以确保输出格式
                    env = os.environ.copy()
                    env['TERM'] = 'dumb'  # 避免颜色和特殊字符
                    
                    self._child = pexpect.spawn(
                        shlex.join([self.joern_path, '--nocolors']),
                        timeout=self.timeout,
                        env=env,
                        encoding='utf-8',
                        codec_errors='replace'
                    )
                    
                    # 设置更大的缓冲区
                    self._child.maxread = 8192
                    
                    # 等待Joern启动完成 - 使用更宽松的匹配
                    startup_patterns = [
                        r'joern>\s*$',  # 标准提示符
                        r'joern>\s*',   # 可能有额外空格
                        pexpect.EOF,
                        pexpect.TIMEOUT
                    ]
                    
                    self.logger.debug("等待Joern启动...")
                    index = self._child.expect(startup_patterns, timeout=60)
                    
                    if index in [0, 1]:  # 成功启动
                        self._last_activity = time.time()
                        self.logger.info("Joern shell 启动成功")
                        self._debug_log("Joern启动成功")
                        
                        # 执行初始化设置
                        self._initialize_shell()
                        return
                        
                    elif index == 2:  # EOF
                        raise RuntimeError("Joern 进程启动后立即退出")
                    else:  # TIMEOUT
                        startup_output = self._child.before if self._child.before else "无输出"
                        self._debug_log(f"启动超时，输出: {startup_output}")
                        raise RuntimeError(f"Joern 启动超时，输出: {startup_output}")
                        
                except Exception as e:
                    self.logger.warning(f"启动尝试 {attempt + 1} 失败: {e}")
                    self._debug_log(f"启动失败: {e}")
                    self._cleanup_connection()
                    if attempt == retry_count - 1:
                        raise RuntimeError(f"无法启动Joern shell，已尝试 {retry_count} 次: {e}")
                    time.sleep(2)  # 增加重试间隔

    def _initialize_shell(self):
        """初始化shell设置"""
        try:
            # 设置输出格式
            init_commands = [
                "// Initialization",  # 注释，确保shell正常
            ]
            
            for cmd in init_commands:
                self._send_raw_command(cmd, expect_output=False)
                
        except Exception as e:
            self.logger.warning(f"Shell初始化失败: {e}")

    def _cleanup_connection(self) -> None:
        """清理连接资源"""
        if self._child is not None:
            try:
                if self._child.isalive():
                    self._child.sendline("exit")
                    self._child.expect(pexpect.EOF, timeout=5)
            except:
                pass
            finally:
                try:
                    self._child.close(force=True)
                except:
                    pass
                self._child = None

    def close_shell(self) -> None:
        """关闭Joern shell连接"""
        with self._lock:
            self._cleanup_connection()
            self.logger.info("Joern shell 已关闭")

    def __enter__(self) -> 'JoernBridge':
        if not self._is_connected():
            self.open_shell()
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
        self.close_shell()

    def _clean_output(self, raw_output: str) -> str:
        """清理命令输出"""
        if not raw_output:
            return ""
            
        # 移除ANSI转义字符
        clean_output = self._ansi_escape.sub('', raw_output)
        # 移除控制字符
        clean_output = self._control_chars.sub('', clean_output)
        # 规范化换行符
        clean_output = self._multi_newlines.sub('\n', clean_output)
        
        # 移除命令回显（如果存在）
        lines = clean_output.split('\n')
        if lines and len(lines) > 1:
            # 如果第一行是命令回显，移除它
            if lines[0].strip().endswith(lines[1].strip()[:20]):  # 简单的回显检测
                lines = lines[1:]
        
        return '\n'.join(lines).strip()

    def _ensure_connection(self) -> None:
        """确保连接可用，如果断开则重连"""
        if not self._is_connected():
            self.logger.warning("检测到连接断开，尝试重新连接")
            self.open_shell()

    def _send_raw_command(self, cmd: str, timeout: Optional[int] = None, expect_output: bool = True) -> str:
        """发送原始命令（内部使用）"""
        if not cmd.strip():
            return ""
            
        cmd_timeout = timeout or self.timeout
        
        try:
            # 确保连接可用
            self._ensure_connection()
            
            if self._child is None or not self._child.isalive():
                raise RuntimeError("无法建立或维持Joern连接")
            
            # 发送命令
            self._debug_log(f"发送命令: {cmd}")
            self._child.sendline(cmd)
            
            if not expect_output:
                return ""
            
            # 等待命令完成 - 使用更灵活的期望模式
            prompt_patterns = [
                r'joern>\s*$',
                r'joern>\s*',
                pexpect.TIMEOUT,
                pexpect.EOF
            ]
            
            index = self._child.expect(prompt_patterns, timeout=cmd_timeout)
            
            if index in [0, 1]:  # 成功执行
                raw_output = self._child.before or ""
                self._last_activity = time.time()
                self._debug_log(f"原始输出: {repr(raw_output)}")
                return raw_output
                
            elif index == 2:  # TIMEOUT
                # 尝试获取部分输出
                partial_output = self._child.before or ""
                self._debug_log(f"超时，部分输出: {repr(partial_output)}")
                self.logger.error(f"命令执行超时({cmd_timeout}秒): {cmd}")
                raise RuntimeError(f"命令执行超时: {cmd}")
                
            else:  # EOF
                self.logger.error("Joern 进程意外退出")
                self._cleanup_connection()
                raise RuntimeError("Joern 进程意外退出")
                
        except Exception as e:
            self._debug_log(f"命令执行错误: {e}")
            raise

    def send_command(self, cmd: str, timeout: Optional[int] = None) -> str:
        """
        发送命令到Joern shell并返回输出
        
        Args:
            cmd: 要执行的命令
            timeout: 命令超时时间（秒），默认使用实例超时时间
            
        Returns:
            命令输出字符串
            
        Raises:
            RuntimeError: 命令执行失败或超时
        """
        if not cmd.strip():
            return ""
        
        # 记录命令历史
        self._command_history.append({
            cmd
        })
        with open('logs/joern_command_history.log', 'a', encoding='utf-8') as f:
            f.write(f"{cmd}\n")
        # 保持最近100条命令
        if len(self._command_history) > 100:
            self._command_history = self._command_history[-100:]
            
        with self._lock:
            try:
                # 清空缓冲区
                self._clear_buffer()
                
                # 发送命令
                raw_output = self._send_raw_command(cmd, timeout)
                
                # 清理输出
                clean_output = self._clean_output(raw_output)
                
                self._debug_log(f"清理后输出: {repr(clean_output)}")
                
                # 验证输出
                if self._is_valid_output(clean_output):
                    return clean_output
                else:
                    self.logger.warning(f"输出验证失败，原始输出: {repr(raw_output)}")
                    return clean_output  # 即使验证失败也返回，让上层处理
                    
            except Exception as e:
                self.logger.error(f"命令执行出错: {e}")
                # 记录更多调试信息
                self._debug_log(f"命令执行异常: {e}")
                self._debug_log(f"连接状态: {self._is_connected()}")
                raise RuntimeError(f"命令执行失败: {e}")

    def _clear_buffer(self):
        """清空输入输出缓冲区"""
        try:
            if self._child and self._child.isalive():
                # 尝试读取并丢弃缓冲区内容
                self._child.read_nonblocking(size=8192, timeout=0.1)
        except:
            pass  # 忽略缓冲区清理错误

    def _is_valid_output(self, output: str) -> bool:
        """验证输出是否有效"""
        if not output:
            return True  # 空输出也是有效的
            
        # 检查是否包含错误信息
        error_indicators = [
            "Exception",
            "Error:",
            "java.lang.",
            "scala.MatchError",
            "CompilerException"
        ]
        
        for indicator in error_indicators:
            if indicator in output:
                self.logger.warning(f"输出包含错误指示器: {indicator}")
                return False
                
        return True

    def send_command_with_retry(self, cmd: str, max_retries: int = 3, timeout: Optional[int] = None) -> str:
        """
        带重试机制的命令发送
        
        Args:
            cmd: 要执行的命令
            max_retries: 最大重试次数
            timeout: 命令超时时间
            
        Returns:
            命令输出字符串
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = self.send_command(cmd, timeout)
                
                # 检查结果是否看起来正确
                if result.strip() == "=~" or not result.strip():
                    if attempt < max_retries - 1:
                        self.logger.debug(f"结果异常，重试 {attempt + 1}/{max_retries}")
                        time.sleep(1)
                        continue
                
                return result
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    self.logger.warning(f"命令执行失败，重试 {attempt + 1}/{max_retries}: {e}")
                    time.sleep(2)
                    # 尝试重新连接
                    try:
                        self._ensure_connection()
                    except:
                        pass
                else:
                    break
        
        raise RuntimeError(f"命令重试失败，最后错误: {last_error}")

    def health_check(self) -> bool:
        """
        健康检查：验证Joern shell是否正常工作
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # 发送简单的测试命令
            result = self.send_command("1 + 1", timeout=10)
            return "2" in result and not result.strip() == "=~"
        except Exception as e:
            self.logger.warning(f"健康检查失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取桥接器状态信息
        
        Returns:
            包含状态信息的字典
        """
        return {
            "connected": self._is_connected(),
            "joern_path": self.joern_path,
            "timeout": self.timeout,
            "last_activity": self._last_activity,
            "uptime": time.time() - self._last_activity if self._is_connected() else 0,
            "command_count": len(self._command_history),
            "debug_mode": self._debug_mode
        }

    def get_command_history(self) -> List[Dict[str, Any]]:
        """获取命令历史"""
        return self._command_history.copy()

    def __del__(self) -> None:
        """析构函数，确保资源清理"""
        try:
            self.close_shell()
        except:
            pass