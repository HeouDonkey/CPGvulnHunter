
from dataclasses import dataclass
from typing import Optional


import logging
from enum import Enum

from CPGvulnHunter.models.cpg.function import Function


@dataclass
class Sanitizer(Function):
    @staticmethod
    def create_from_function(function: Function) -> "Sanitizer":
        """
        工厂函数：从Function创建Sanitizer
        :param function: Function实例
        :return: Sanitizer实例
        """
        # 使用字典解包，更简洁且不易出错
        return Sanitizer(**function.__dict__)

    def getQuery(self) -> str:
        """
        获取查询命令字符串
        :return: 查询命令字符串
        """
        return ''

