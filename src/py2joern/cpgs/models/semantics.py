from dataclasses import dataclass
from typing import List, Tuple, Optional
import json
import os


"""
import io.joern.dataflowengineoss.semanticsloader.FlowSemantic
import io.shiftleft.semanticcpg.layers.LayerCreatorOptions
import io.joern.dataflowengineoss.layers.dataflows.OssDataFlowOptions
import io.shiftleft.semanticcpg.layers.*
import io.joern.dataflowengineoss.*
import io.joern.dataflowengineoss.layers.dataflows.*
Overlays.removeLastOverlayName(cpg)
val extraFlows = List(
FlowSemantic.from("strncpy",List((3, 1)), regex = false)
)
val context = new LayerCreatorContext(cpg)
val options = new OssDataFlowOptions(semantics = DefaultSemantics().plus(extraFlows))
new OssDataFlow(options).run(context)
cpg.method.fullName("dangerous_sink").parameter.index(1).reachableByFlows(cpg.method.fullName("input").methodReturn).p

val engineConfig = EngineConfig(maxCallDepth = 20)
implicit val context: EngineContext = EngineContext(config = engineConfig)

"""




"""
import io.joern.dataflowengineoss.*
import io.joern.dataflowengineoss.semanticsloader.*
import io.joern.dataflowengineoss.queryengine.*

val extraFlows = List(
FlowSemantic.from("strncpy",List((1, 2)), regex = false)
)
// 创建引擎上下文
implicit val semantics: Semantics = DefaultSemantics().plus(extraFlows)
implicit val context: EngineContext = EngineContext(semantics = semantics)

// 直接在查询中使用
cpg.method.fullName("dangerous_sink").parameter.index(1).reachableByFlows(cpg.method.fullName("input").methodReturn).p
"""


@dataclass
class ParameterFlow:
    """参数间数据流映射规则"""
    from_param: int    # 源参数索引（-1表示返回值）
    to_param: int      # 目标参数索引（-1表示返回值）

    def from_json(json_data: dict) -> 'ParameterFlow':
        """
        从JSON数据创建ParameterFlow对象
        """
        return ParameterFlow(
            from_param=json_data['from'],
            to_param=json_data['to']
        )


@dataclass
class Semantic:
    """单个函数的语义规则,一个函数之应该有一个semantic"""
    method: str          # 方法全名
    param_flows: List[ParameterFlow]  # 参数间数据流映射列表
    is_regex: bool = False         # 是否将方法全名解释为正则表达式

    def __init__(self, method_full_name: str =None, param_flows: List[ParameterFlow] = None, is_regex: bool = False):
        self.method = method_full_name
        self.param_flows = param_flows 
        self.is_regex = is_regex


    def to_Joern_script(self) -> str:
        """
        将单个语义规则转换为Joern脚本格式
        """
        flows_str = ', '.join(f'({flow.from_param}, {flow.to_param})' for flow in self.param_flows)
        return f'FlowSemantic.from("{self.method}", List({flows_str}), regex = {str(self.is_regex).lower()})'


    
@dataclass
class Semantics:
    """一个cpg中所有外部函数的semantic规则"""
    
    def __init__(self):
        self.semantic_list: List[Semantic] = []
    
    """
    flow的用法:
        FlowSemantic.from(
        "^path.*<module>\\.sanitizer$", // Method full name
        List((1, 1)), // Flow mappings
        regex = true  // Interpret the method full name as a regex string
    )
    """

    def add_senmatic(self,semantic: Semantic) -> None:
        """
        添加单个语义规则
        
        Args:
            semantic: 要添加的语义规则
        """
        self.semantic_list.append(semantic)

    def get_extraFlows(self) -> str:
        """
        生成 Joern FlowSemantic 格式的语义规则字符串
        
        Returns:
            str: Joern 格式的 FlowSemantic 规则字符串
        """
        if not self.semantic_list:
            return ""
        
        semantic_parts = []
        for semantic in self.semantic_list:
            
            # 生成单个 FlowSemantic 规则
            semantic_rule = semantic.to_Joern_script()
            semantic_parts.append(semantic_rule)
        
        # 组合所有规则
        return "val extraFlows = List(" + ",\n".join(semantic_parts) + ")"
    




