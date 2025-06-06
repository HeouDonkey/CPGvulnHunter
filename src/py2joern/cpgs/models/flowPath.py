from dataclasses import dataclass
import logging
from typing import List, Optional, Dict, Any
from enum import Enum
import json

class NodeType(Enum):
    """节点类型枚举"""
    METHOD_PARAMETER_IN = "METHOD_PARAMETER_IN"      # 方法输入参数节点 - 表示函数/方法的输入参数
    METHOD_PARAMETER_OUT = "METHOD_PARAMETER_OUT"    # 方法输出参数节点 - 表示函数/方法的输出参数（引用传递）
    METHOD_RETURN = "METHOD_RETURN"                  # 方法返回值节点 - 表示函数/方法的返回值
    CALL = "CALL"                                    # 函数调用节点 - 表示对函数或方法的调用
    IDENTIFIER = "IDENTIFIER"                        # 标识符节点 - 表示变量名、函数名等标识符
    LITERAL = "LITERAL"                              # 字面量节点 - 表示常量值（如字符串、数字等）
    LOCAL = "LOCAL"                                  # 局部变量节点 - 表示局部变量的声明或定义
    BLOCK = "BLOCK"                                  # 代码块节点 - 表示代码块（如if块、循环体等）
    CONTROL_STRUCTURE = "CONTROL_STRUCTURE"          # 控制结构节点 - 表示控制流语句（如if、for、while等）
    UNKNOWN = "UNKNOWN"                              # 未知类型节点 - 无法识别或不在上述类型中的节点

@dataclass
class FlowNode:
    """数据流节点，表示数据流路径中的一个节点"""
    
    # 基本信息
    node_id: int                          # 节点ID (_id)
    label: str                           # 节点标签 (_label)
    code: str                            # 节点代码
    
    # 位置信息
    line_number: Optional[int] = None     # 行号
    column_number: Optional[int] = None   # 列号
    
    # 类型信息
    type_full_name: Optional[str] = None  # 完整类型名
    possible_types: List[str] = None      # 可能的类型列表
    dynamic_type_hint_full_name: List[str] = None
    
    # 节点特定属性
    name: Optional[str] = None            # 节点名称
    order: Optional[int] = None           # 顺序
    
    # 参数相关（如果是参数节点）
    index: Optional[int] = None           # 参数索引
    evaluation_strategy: Optional[str] = None  # 求值策略
    is_variadic: Optional[bool] = None    # 是否可变参数
    argument_index: Optional[int] = None  # 参数索引
    
    # 方法相关（如果是方法调用）
    signature: Optional[str] = None       # 方法签名
    method_full_name: Optional[str] = None # 方法全名
    dispatch_type: Optional[str] = None   # 调度类型
    
    # 流路径相关
    call_site_stack: List[Any] = None     # 调用站点栈
    visible: bool = True                  # 是否可见
    is_output_arg: bool = False           # 是否为输出参数
    out_edge_label: str = ""              # 输出边标签
    
    # 其他属性
    properties: Dict[str, Any] = None     # 其他属性
    
    def __post_init__(self):
        if self.possible_types is None:
            self.possible_types = []
        if self.dynamic_type_hint_full_name is None:
            self.dynamic_type_hint_full_name = []
        if self.call_site_stack is None:
            self.call_site_stack = []
        if self.properties is None:
            self.properties = {}
    
    @classmethod
    def from_path_node(cls, path_node_data: Dict[str, Any]) -> 'FlowNode':
        """从Joern路径节点数据创建FlowNode实例"""
        node_data = path_node_data.get('node', {})
        
        return cls(
            # 基本信息
            node_id=node_data.get('_id', 0),
            label=node_data.get('_label', ''),
            code=node_data.get('code', ''),
            
            # 位置信息
            line_number=node_data.get('lineNumber'),
            column_number=node_data.get('columnNumber'),
            
            # 类型信息
            type_full_name=node_data.get('typeFullName'),
            possible_types=node_data.get('possibleTypes', []),
            dynamic_type_hint_full_name=node_data.get('dynamicTypeHintFullName', []),
            
            # 节点特定属性
            name=node_data.get('name'),
            order=node_data.get('order'),
            
            # 参数相关
            index=node_data.get('index'),
            evaluation_strategy=node_data.get('evaluationStrategy'),
            is_variadic=node_data.get('isVariadic'),
            argument_index=node_data.get('argumentIndex'),
            
            # 方法相关
            signature=node_data.get('signature'),
            method_full_name=node_data.get('methodFullName'),
            dispatch_type=node_data.get('dispatchType'),
            
            # 流路径相关
            call_site_stack=path_node_data.get('callSiteStack', []),
            visible=path_node_data.get('visible', True),
            is_output_arg=path_node_data.get('isOutputArg', False),
            out_edge_label=path_node_data.get('outEdgeLabel', ''),
            
            # 其他属性
            properties={k: v for k, v in node_data.items() 
                       if k not in ['_id', '_label', 'code', 'lineNumber', 'columnNumber',
                                   'typeFullName', 'possibleTypes', 'dynamicTypeHintFullName',
                                   'name', 'order', 'index', 'evaluationStrategy', 'isVariadic',
                                   'argumentIndex', 'signature', 'methodFullName', 'dispatchType']}
        )
    
    @property
    def node_type(self) -> NodeType:
        """获取节点类型"""
        try:
            return NodeType(self.label)
        except ValueError:
            return NodeType.UNKNOWN
    
    def is_source(self) -> bool:
        """判断是否为数据源节点"""
        return self.node_type in [NodeType.METHOD_PARAMETER_IN, NodeType.CALL, NodeType.METHOD_RETURN]
    
    def is_sink(self) -> bool:
        """判断是否为数据汇聚节点"""
        return self.node_type in [NodeType.CALL, NodeType.METHOD_PARAMETER_IN]
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        if self.name:
            return self.name
        elif self.method_full_name:
            return self.method_full_name
        else:
            return self.code[:20] + "..." if len(self.code) > 20 else self.code
    
    def get_location_str(self) -> str:
        """获取位置字符串"""
        if self.line_number:
            location = f":{self.line_number}"
            if self.column_number:
                location += f":{self.column_number}"
            return location
        return ""
    
    def __str__(self) -> str:
        display_name = self.get_display_name()
        location = self.get_location_str()
        edge_info = f" -> {self.out_edge_label}" if self.out_edge_label else ""
        
        return f"{display_name}({self.label}){location}{edge_info}"

@dataclass
class FlowPath:
    """数据流路径，表示从源到汇的完整数据流"""
    
    nodes: List[FlowNode]                 # 路径中的所有节点
    
    # 路径属性
    is_vulnerable: bool = False           # 是否为漏洞路径
    confidence: float = 0.0               # 置信度 (0.0 - 1.0)
    vulnerability_type: Optional[str] = None  # 漏洞类型
    description: Optional[str] = None     # 路径描述
    
    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
    
    @classmethod
    def from_joern_path(cls, path_data: Dict[str, Any]) -> 'FlowPath':
        """从Joern路径数据创建FlowPath实例"""
        path_nodes = path_data.get('path', [])
        nodes = [FlowNode.from_path_node(node_data) for node_data in path_nodes]
        
        return cls(nodes=nodes)
    
    @property
    def path_length(self) -> int:
        """路径长度"""
        return len(self.nodes)
    
    @property
    def source(self) -> Optional[FlowNode]:
        """获取源节点（第一个节点）"""
        return self.nodes[0] if self.nodes else None
    
    @property
    def sink(self) -> Optional[FlowNode]:
        """获取汇聚节点（最后一个节点）"""
        return self.nodes[-1] if self.nodes else None
    
    @property
    def intermediate_nodes(self) -> List[FlowNode]:
        """获取中间节点"""
        return self.nodes[1:-1] if len(self.nodes) > 2 else []
    
    @property
    def source_info(self) -> str:
        """获取源节点信息"""
        if self.source:
            return f"{self.source.get_display_name()} (line {self.source.line_number})"
        return "Unknown source"
    
    @property
    def sink_info(self) -> str:
        """获取汇聚节点信息"""
        if self.sink:
            return f"{self.sink.get_display_name()} (line {self.sink.line_number})"
        return "Unknown sink"
    
    def get_path_summary(self) -> str:
        """获取路径摘要"""
        summary = f"Data flow: {self.source_info} -> {self.sink_info}"
        if self.vulnerability_type:
            summary += f" [{self.vulnerability_type}]"
        if self.confidence > 0:
            summary += f" (confidence: {self.confidence:.2f})"
        return summary
    
    def get_detailed_path(self) -> str:
        """获取详细的路径描述"""
        path_steps = []
        for i, node in enumerate(self.nodes):
            step = f"  {i+1}. {node}"
            path_steps.append(step)
        
        return "\n".join(path_steps)
    
    def get_line_numbers(self) -> List[int]:
        """获取路径经过的所有行号"""
        return [node.line_number for node in self.nodes if node.line_number is not None]
    
    def has_node_type(self, node_type: NodeType) -> bool:
        """检查路径是否包含特定类型的节点"""
        return any(node.node_type == node_type for node in self.nodes)
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[FlowNode]:
        """获取特定类型的所有节点"""
        return [node for node in self.nodes if node.node_type == node_type]
    
    


    def __str__(self) -> str:
        if not self.nodes:
            return "Empty FlowPath"
        
        node_summary = " -> ".join([node.get_display_name() for node in self.nodes])
        return f"FlowPath({self.path_length} nodes): {node_summary}"

@dataclass
class DataFlowResult:
    """数据流分析结果"""
    
    flows: List[FlowPath]                 # 所有发现的数据流路径
    analysis_time: float = 0.0            # 分析时间（秒）
    
    def __post_init__(self):
        if self.flows is None:
            self.flows = []
    
    @classmethod
    def from_joern_result(cls, json_str: str) -> 'DataFlowResult':
        """从Joern的JSON结果创建DataFlowResult实例"""
        try:
            # 解析JSON字符串
            data = json.loads(json_str)
            flows = []
            
            if isinstance(data, list):
                for flow_data in data:
                    if isinstance(flow_data, dict) and 'path' in flow_data:
                        flow = FlowPath.from_joern_path(flow_data)
                        flows.append(flow)
                        logging.debug(f"添加数据流路径: {flow.get_path_summary()}")
            
            return cls(flows=flows)
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return cls(flows=[])
    
    @property
    def flow_count(self) -> int:
        """数据流总数"""
        return len(self.flows)
    
    @property
    def vulnerable_flows(self) -> List[FlowPath]:
        """获取所有可能的漏洞流"""
        return [flow for flow in self.flows if flow.is_vulnerable]
    
    @property
    def vulnerable_count(self) -> int:
        """漏洞流数量"""
        return len(self.vulnerable_flows)
    
    @property
    def all_sources(self) -> List[FlowNode]:
        """获取所有数据源"""
        sources = []
        for flow in self.flows:
            if flow.source and flow.source not in sources:
                sources.append(flow.source)
        return sources
    
    @property
    def all_sinks(self) -> List[FlowNode]:
        """获取所有数据汇聚点"""
        sinks = []
        for flow in self.flows:
            if flow.sink and flow.sink not in sinks:
                sinks.append(flow.sink)
        return sinks
    
    def get_flows_by_type(self, vulnerability_type: str) -> List[FlowPath]:
        """根据漏洞类型获取流"""
        return [flow for flow in self.flows 
                if flow.vulnerability_type == vulnerability_type]
    
    def get_flows_by_source_type(self, node_type: NodeType) -> List[FlowPath]:
        """根据源节点类型获取流"""
        return [flow for flow in self.flows 
                if flow.source and flow.source.node_type == node_type]
    
    def get_flows_by_sink_type(self, node_type: NodeType) -> List[FlowPath]:
        """根据汇聚节点类型获取流"""
        return [flow for flow in self.flows 
                if flow.sink and flow.sink.node_type == node_type]
    
    def get_summary(self) -> str:
        """获取分析结果摘要"""
        return (f"Data Flow Analysis Result:\n"
                f"  Total flows: {self.flow_count}\n"
                f"  Vulnerable flows: {self.vulnerable_count}\n"
                f"  Sources: {len(self.all_sources)}\n"
                f"  Sinks: {len(self.all_sinks)}\n"
                f"  Analysis time: {self.analysis_time:.2f}s")
    
    def get_detailed_report(self) -> str:
        """获取详细报告"""
        report = [self.get_summary(), "\n" + "="*50]
        
        for i, flow in enumerate(self.flows, 1):
            report.append(f"\nFlow {i}:")
            report.append(f"  {flow.get_path_summary()}")
            report.append(f"  Path details:")
            report.append(flow.get_detailed_path())
        
        return "\n".join(report)