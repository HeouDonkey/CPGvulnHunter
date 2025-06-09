
from dataclasses import dataclass
from typing import Optional


import logging
from enum import Enum

from CPGvulnHunter.models.cpg.function import Function


@dataclass
class Sink(Function):
    index: Optional[int] = None # 在参数列表中的索引

    """
    Basic Syntax #

    The basic syntax of semantics is the method full name, 
    followed by argument pairs denoting source-destination pairs, e.g., 
    "foo" 1->-1 2->3. -1 is the return value, 
    and 0 is the receiver/base of the call (relevant for object-oriented programming languages), 
    where everything > 0 is the call’s arguments.

    Following from the example above, 
    the semantic definition for x = foo.bar(a, b) would look something like Foo.
    bar 1->-1 0->0 1->1 2->2. While the first entry is rather intuitive (flow from argument 1 propagates to the return value), 
    the last three simply reiterate that the data-flow in the other arguments are not to be killed at this call site.


    """
    @staticmethod
    def create_from_function(function: Function, index = None) -> "Sink":
        """
        工厂函数：从Function创建Sink
        :param function: Function实例
        :param index: sink索引
        :return: Sink实例
        """
        return Sink(
            name=function.name,
            ast_parent_full_name=function.ast_parent_full_name,
            ast_parent_type=function.ast_parent_type,
            code=function.code,
            column_number=function.column_number,
            column_number_end=function.column_number_end,
            filename=function.filename,
            full_name=function.full_name,
            generic_signature=function.generic_signature,
            hash_value=function.hash_value,
            is_external=function.is_external,
            line_number=function.line_number,
            line_number_end=function.line_number_end,
            offset=function.offset,
            offset_end=function.offset_end,
            order=function.order,
            signature=function.signature,
            index=index
        )

    def getQuery(self) -> str:
        """
        获取查询命令字符串
        :return: 查询命令字符串
        """
        if self.index is not None:
            # return value
            if self.index == -1:
                return self.findReturnValue()
            if self.index >0:
                return self.findParameter(self.index)
            if self.index ==0:
                #todo  面向对象语言的自身污染。
                pass
            else:
                logging.error("非法的方法索引！")
            

