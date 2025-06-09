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
            self.logger.setLevel(logging.INFO)

    def _is_connected(self) -> bool:
        """检查连接是否有效"""
        return self._child is not None and self._child.isalive()

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
                    
                    self._child = pexpect.spawn(
                        shlex.join([self.joern_path, '--nocolors']),
                        timeout=self.timeout
                    )
                    
                    # 等待Joern启动完成
                    index = self._child.expect([b"joern> ", pexpect.EOF, pexpect.TIMEOUT], timeout=30)
                    
                    if index == 0:  # 成功启动
                        self._last_activity = time.time()
                        self.logger.info("Joern shell 启动成功")
                        return
                    elif index == 1:  # EOF
                        raise RuntimeError("Joern 进程启动后立即退出")
                    else:  # TIMEOUT
                        raise RuntimeError("Joern 启动超时")
                        
                except Exception as e:
                    self.logger.warning(f"启动尝试 {attempt + 1} 失败: {e}")
                    self._cleanup_connection()
                    if attempt == retry_count - 1:
                        raise RuntimeError(f"无法启动Joern shell，已尝试 {retry_count} 次")
                    time.sleep(1)  # 重试间隔

    def _cleanup_connection(self) -> None:
        """清理连接资源"""
        if self._child is not None:
            try:
                if self._child.isalive():
                    self._child.sendline(b"exit")
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
        # 移除ANSI转义字符
        clean_output = self._ansi_escape.sub('', raw_output)
        # 移除控制字符
        clean_output = self._control_chars.sub('', clean_output)
        # 规范化换行符
        clean_output = self._multi_newlines.sub('\n', clean_output)
        return clean_output.strip()

    def _ensure_connection(self) -> None:
        """确保连接可用，如果断开则重连"""
        if not self._is_connected():
            self.logger.warning("检测到连接断开，尝试重新连接")
            self.open_shell()

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
            
        cmd_timeout = timeout or self.timeout
        
        with self._lock:
            try:
                import pexpect
                
                # 确保连接可用
                self._ensure_connection()
                
                # 再次检查连接是否成功建立
                if self._child is None or not self._child.isalive():
                    raise RuntimeError("无法建立或维持Joern连接")
                
                # 清空输入输出缓冲区
                self._child.sendline(b"")
                try:
                    self._child.expect_exact(b"joern> ", timeout=5)
                    # 丢弃缓冲区内容
                    try:
                        self._child.read_nonblocking(size=8192, timeout=0.1)
                    except:
                        pass
                except pexpect.exceptions.TIMEOUT:
                    self.logger.warning("清理缓冲区时超时，继续执行命令")
                
                # 发送命令前再次检查连接
                if self._child is None or not self._child.isalive():
                    raise RuntimeError("连接在命令发送前断开")
                
                # 发送命令
                self.logger.debug(f"执行命令: {cmd}")
                self._child.sendline(cmd.encode('utf-8'))
                
                # 等待命令完成
                try:
                    self._child.expect_exact(b"joern> ", timeout=cmd_timeout)
                    
                    # 获取输出
                    raw_output = self._child.before
                    if raw_output:
                        output_str = raw_output.decode('utf-8', errors='replace')
                        clean_output = self._clean_output(output_str)
                        self._last_activity = time.time()
                        return clean_output
                    return ""
                    
                except pexpect.exceptions.TIMEOUT:
                    self.logger.error(f"命令执行超时({cmd_timeout}秒): {cmd}")
                    # 尝试获取部分输出
                    try:
                        partial_output = self._child.before
                        if partial_output:
                            output_str = partial_output.decode('utf-8', errors='replace')
                            self.logger.debug(f"超时时的部分输出: {repr(output_str[:200])}")
                    except:
                        pass
                    raise RuntimeError(f"命令执行超时: {cmd}")
                    
                except pexpect.exceptions.EOF:
                    self.logger.error("Joern 进程意外退出")
                    self._cleanup_connection()
                    raise RuntimeError("Joern 进程意外退出")
                    
            except Exception as e:
                self.logger.error(f"命令执行出错: {e}")
                raise RuntimeError(f"命令执行失败: {e}")

    def health_check(self) -> bool:
        """
        健康检查：验证Joern shell是否正常工作
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # 发送简单的测试命令
            result = self.send_command("1 + 1", timeout=10)
            return "2" in result
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
            "uptime": time.time() - self._last_activity if self._is_connected() else 0
        }

    def __del__(self) -> None:
        """析构函数，确保资源清理"""
        try:
            self.close_shell()
        except:
            pass