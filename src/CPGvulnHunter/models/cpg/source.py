from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
import json

from CPGvulnHunter.models.cpg.function import Function

@dataclass
class Source(Function):
    index: Optional[int] = None # 在参数列表中的索引

    @staticmethod
    def create_from_function(function: Function, index = None) -> "Source":

        return Source(
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
            index=int(index)
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
                return self.findParameterOut(self.index)
            if self.index ==0:
                #todo  面向对象语言的自身污染。
                pass
            else:
                logging.error("非法的方法索引！")


    def getSourceInfo(self) -> str:
        """
        获取源函数信息
        :return: 源函数信息字符串
        """
        source_info = f"Source Function: {self.name}, Full Name: {self.full_name}, Index: {self.index if self.index is not None else 'N/A'}"
        source_info += f", External: {self.is_external}, Signature: {self.signature}"
        source_info += f", Line: {self.line_number}-{self.line_number_end}, Column: {self.column_number}-{self.column_number_end}"
        source_info += f", Offset: {self.offset}-{self.offset_end}, Order: {self.order}"
        source_info += f", AST Parent: {self.ast_parent_full_name} ({self.ast_parent_type})"
        source_info += f", Code Snippet: {self.code[:50]}..." if self.code else ", Code Snippet: N/A"
        return f"Source Function: {self.name}, Full Name: {self.full_name}, Index: {self.index if self.index is not None else 'N/A'}"

    def to_dict(self):
        """
        将Source对象转换为字典
        """
        return {
            "name": self.name,
            "ast_parent_full_name": self.ast_parent_full_name,
            "ast_parent_type": self.ast_parent_type,
            "code": self.code,
            "column_number": self.column_number,
            "column_number_end": self.column_number_end,
            "filename": self.filename,
            "full_name": self.full_name,
            "generic_signature": self.generic_signature,
            "hash_value": self.hash_value,
            "is_external": self.is_external,
            "line_number": self.line_number,
            "line_number_end": self.line_number_end,
            "offset": self.offset,
            "offset_end": self.offset_end,
            "order": self.order,
            "signature": self.signature,
            "index": self.index
        }

    def toJson(self, indent: Optional[int] = None) -> str:
        """
        将Source对象转换为JSON字符串
        
        Args:
            indent: JSON缩进级别，None表示紧凑格式
            
        Returns:
            str: JSON格式的字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, default=str)

    @classmethod
    def fromJson(cls, json_str: str) -> 'Source':
        """
        从JSON字符串创建Source对象
        
        Args:
            json_str: JSON格式的字符串
            
        Returns:
            Source: Source对象实例
        """
        data = json.loads(json_str)
        return cls(**data)