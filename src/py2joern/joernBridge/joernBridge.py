from typing import Optional, List, Dict
from dataclasses import dataclass
import os
import re
import json
import shutil
import logging  

class JoernBridge:
    """
    仅用于与 Joern 命令行交互的桥接类
    """
    def __init__(self, joern_path: str = "joern"):
        self.joern_path = joern_path if os.path.isabs(joern_path) else shutil.which(joern_path) or joern_path
        self._child = None
        self.open_shell()

    def open_shell(self, timeout: int = 1000):
        if self._child is not None and self._child.isalive():
            # 已经有可用的 shell，不重复打开
            return
        try:
            import pexpect
        except ImportError:
            raise ImportError("请先安装pexpect库: pip install pexpect")
        import shlex
        # 关闭已存在但失效的 shell
        if self._child is not None:
            self.close_shell()
        self._child = pexpect.spawn(
            shlex.join([self.joern_path, '--nocolors']),
            timeout=timeout
        )
        try:
            self._child.expect_exact([b"joern> ", pexpect.EOF, pexpect.TIMEOUT])
        except pexpect.exceptions.TIMEOUT:
            print(f"[警告] Joern 启动超时，尝试继续...")
        except pexpect.exceptions.EOF:
            print(f"[错误] Joern 进程意外退出")

    def close_shell(self):
        if self._child is not None:
            try:
                if self._child.isalive():
                    self._child.sendline(b"exit")
            except Exception:
                pass
            try:
                self._child.close()
            except Exception:
                pass
            self._child = None

    def __enter__(self):
        if self._child is None or not self._child.isalive():
            self.open_shell()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_shell()


    def read_before(self) -> str:
        """
        读取当前 shell 的输出缓冲区内容
        """
        if self._child is None or not self._child.isalive():
            raise RuntimeError("Joern shell 未打开或已关闭")
        output = self._child.before
        if output:
            return output.decode('utf-8', errors='replace')
        return ""

    def send_command(self, cmd: str) -> str:
        import pexpect
        import time
        
        # 确保 shell 可用
        if self._child is None or not self._child.isalive():
            self.open_shell()
        
        try:            
            # 更彻底地清空缓冲区
            try:
                # 多次尝试清空缓冲区
                for _ in range(3):
                    self._child.read_nonblocking(size=4096, timeout=0.1)
            except:
                pass
            
            # 发送一个空行确保提示符出现
            self._child.sendline(b"")
            try:
                self._child.expect_exact(b"joern> ", timeout=5)
            except:
                pass
            
            # 再次清空缓冲区
            try:
                self._child.read_nonblocking(size=4096, timeout=0.1)
            except:
                pass
            
            # 发送实际命令
            self._child.sendline(cmd.encode('utf-8'))
            
            # 等待命令执行完成
            try:
                self._child.expect_exact(b"joern> ", timeout=120)
                
                output = self._child.before
                if output:
                    output_str = output.decode('utf-8', errors='replace')
                    # 清理ANSI转义字符和控制字符
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    clean_output = ansi_escape.sub('', output_str)
                    # 移除回车符、换行符和其他控制字符
                    clean_output = re.sub(r'[\r\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]+', '', clean_output)
                    # 规范化换行符
                    clean_output = re.sub(r'\n+', '\n', clean_output).strip()
                    
                    return clean_output
                return ""
                
            except pexpect.exceptions.TIMEOUT:
                logging.error(f"命令执行超时（120秒）: {cmd}")
                try:
                    output = self._child.before
                    if output:
                        output_str = output.decode('utf-8', errors='replace')
                        logging.error(f"超时时的输出: {repr(output_str)}")
                except:
                    pass
                raise RuntimeError("命令执行超时")
                
            except pexpect.exceptions.EOF:
                logging.error("Joern 进程意外退出")
                self.close_shell()
                raise RuntimeError("Joern 进程意外退出")
                
        except Exception as e:
            logging.error(f"命令执行失败: {e}")
            if isinstance(e, (pexpect.exceptions.TIMEOUT, pexpect.exceptions.EOF, RuntimeError)):
                raise
            return ""