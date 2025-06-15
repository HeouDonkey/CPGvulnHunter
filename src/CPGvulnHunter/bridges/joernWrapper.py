import json
import re
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from abc import ABC, abstractmethod

from CPGvulnHunter.models.cpg.flowPath import DataFlowResult, FlowNode
from CPGvulnHunter.models.cpg.function import Function, Parameter
from CPGvulnHunter.models.cpg.joernQueryResult import JoernQueryResult
from CPGvulnHunter.models.cpg.semantics import Semantics
from CPGvulnHunter.models.cpg.sink import Sink
from CPGvulnHunter.models.cpg.source import Source
from .joernBridge import JoernBridge

#这个类不应该做任何的返回检查，所有的命令执行检查都应在JoernBridge中完成
class JoernWrapper:
    """Joern交互包装器 - 封装所有Joern操作"""
    
    def __init__(self, joern_path: str) -> None:
        self.joern = JoernBridge(joern_path)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Ensure logger uses the level from config
        self.logger.setLevel(logging.getLogger().level)
        self._semantics_applied: bool = False
        # 编译常用的正则表达式
        self._json_pattern = re.compile(r'"""(.*?)"""', re.DOTALL)
        
    def __enter__(self) -> 'JoernWrapper':
        return self
        
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], 
                exc_tb: Optional[object]) -> None:
        self.close()
        
    def close(self) -> None:
        """关闭连接"""
        if hasattr(self.joern, 'close_shell'):
            self.joern.close_shell()
    
    # === 核心执行方法 ===
    
    def _execute_command(self, command: str, timeout: Optional[int] = None) -> dict | None:
        """执行Joern命令的基础方法"""
        try:
            self.logger.debug(f"执行命令: {command}")
            result = self.joern.send_command(command, timeout)
            self.logger.debug(f"命令结果: {result}")
            json_result = self._extract_json_data(result)
            return json_result
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"命令执行异常: {error_msg}")
            return None
    
    def _extract_json_data(self, raw_result: str) -> Optional[dict]:
        """从Joern输出中提取JSON数据"""
        try:
            match = self._json_pattern.search(raw_result)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            return None
        except (json.JSONDecodeError, AttributeError) as e:
            self.logger.warning(f"JSON解析失败: {e}")
            return None
    
    
    # === CPG基础操作 ===
    
    def import_code(self, src_path: str) -> JoernQueryResult:
        """导入源代码"""
        cmd = f'importCode("{src_path}")'
        self.logger.info(f"导入代码: {src_path}")
        self._execute_command(cmd)
    
    def get_function_full_names(self, cpg_var: str = "cpg") -> List[str]|None:
        """获取所有函数名"""
        cmd = f"{cpg_var}.method.fullName.toJsonPretty"
        data = self._execute_command(cmd)
        if data and isinstance(data, list):
            return data
        self.logger.warning("未能获取函数名列表")
        return None
    
    def get_function_by_full_name(self, function_full_name: str, cpg_var: str = "cpg") -> Optional[Function]:
        """
        get single function by full name
        :param function_full_name: full name of the function
        :param cpg_var: CPG variable name, default is "cpg"
        :return: Function object or None if not found
        """
        cmd = f'{cpg_var}.method.fullName("{function_full_name}").toJsonPretty'
        data = self._execute_command(cmd)
        if data:
            # 如果是列表，取第一个
            if isinstance(data, list) and data:
                if len(data) > 1:
                    self.logger.warning(f"获取函数数据时返回了多个结果: {data}")
                    self.logger.warning(f"使用第一个结果: {data[0]}")
                return Function.from_json(data[0])
            return  Function.from_json(data)
        self.logger.error(f"未找到函数: {function_full_name}")
        return None


    def _get_function_by_id(self, id: str, cpg_var: str = "cpg") -> Optional[str]|None:
        """
        get single function by full name
        :param function_full_name: full name of the function
        :param cpg_var: CPG variable name, default is "cpg"
        :return: Function object or None if not found
        """
        cmd= f'{cpg_var}.id({id}).head._cfgIn.head.asInstanceOf[CfgNode].method.toList.toJsonPretty'
        data = self._execute_command(cmd)
        self.logger.debug(f"通过函数ID {id} 的获取函数的结果: {data}")   
        if data:
            # 如果是列表，取第一个
            if isinstance(data, list) and data:
                if len(data) > 1:
                    self.logger.warning(f"获取函数数据时返回了多个结果: {data}")
                    self.logger.warning(f"使用第一个结果: {data[0]}")
                return Function.from_json(data[0])
            return  Function.from_json(data)
        else:
            self.logger.error(f"未找到函数ID: {id}")
            return None


    def get_parameter(self, function: Function, cpg_var: str = "cpg") -> List[Parameter]:
        """
        返回函数的参数列表。
        :param function: 函数对象
        :return: 参数列表
        """
        cmd = function.generateParameterQuery()
        parameter_list_json = self._execute_command(cmd)
        parameter_list = []
        if parameter_list_json is not None:
            # 创建 Parameter 对象列表
            for param_json in parameter_list_json:
                p = Parameter.from_json(param_json)
                parameter_list.append(p)
        else:
            self.logger.error(f"未找到参数")
        return parameter_list

    def find_useage(self, function: Function) -> str:
        "查找函数调用点的使用情况"
        result = function.generateUseageQuery()
        match = re.search(r'"""(.*?)"""', result, re.DOTALL)
        if match:
            json_str = match.group(1)
            useage_data = json.loads(json_str)
            self.logger.debug(f"函数 {function.full_name} 的使用情况: {useage_data}")
            return useage_data
        else:
            self.logger.error(f"未找到函数 {function.full_name} 的使用情况")
            return ''  

    # === 语义分析操作 ===

    
    def import_dataflow_classes(self) -> bool:
        """导入数据流分析所需的类"""
        imports = [
            "import io.joern.dataflowengineoss.*",
            "import io.joern.dataflowengineoss.semanticsloader.*", 
            "import io.joern.dataflowengineoss.queryengine.*",
        ]
        
        for import_cmd in imports:
            result = self._execute_command(import_cmd)
            if result == None:
                self.logger.error(f"导入失败: {import_cmd}")
                return False
        
        return True
    
    def define_extra_flows(self, extra_flows: str) -> bool:
        """定义额外的数据流规则"""
        if not extra_flows.strip():
            return True
        
        result = self._execute_command(extra_flows)
        if result == None:
            self.logger.error("定义额外数据流规则失败: 结果为空")
            return False
  
        return True
    
    def create_semantics_context(self) -> bool:
        """创建语义上下文"""
        cmd = "implicit val semantics: Semantics = DefaultSemantics().plus(extraFlows)"
        result = self._execute_command(cmd)
        if result == None:
            self.logger.error(f"语义上下文创建失败: {result.error_message}")
            return False
        
        return True
    
    def create_engine_context(self, max_call_depth: int = 40) -> bool:
        """创建引擎上下文"""
        cmd = f"implicit val engineConfig: EngineConfig = EngineConfig(maxCallDepth = {max_call_depth})\n"
        cmd += f"implicit val context: EngineContext = EngineContext(semantics = semantics, config = engineConfig)"
        result = self._execute_command(cmd)
        if result == None:
            self.logger.error(f"引擎上下文创建失败: {result.error_message}")
            return False
        
        return True
    
    def apply_semantics(self, semantics: Semantics) -> bool:
        extra_flows = semantics.get_extraFlows()
        """应用语义规则（完整流程）"""
        try:
            self.logger.info("开始应用语义规则...")
            
            # 1. 测试连接
            if not self.joern.health_check():
                self.logger.error("连接测试失败")
                return False
            
            # 2. 导入必要类
            if not self.import_dataflow_classes():
                self.logger.error("导入数据流类失败")
                return False
            
            # 3. 定义语义规则
            if not self.define_extra_flows(extra_flows):
                self.logger.error("定义语义规则失败")
                return False
            
            # 4. 创建语义上下文
            if not self.create_semantics_context():
                self.logger.error("创建语义上下文失败")
                return False
            
            # 5. 创建引擎上下文
            if not self.create_engine_context():
                self.logger.error("创建引擎上下文失败")
                return False
            
            self._semantics_applied = True
            self.logger.info("语义规则应用成功")
            return True
            
        except Exception as e:
            self.logger.error(f"语义规则应用异常: {e}")
            return False
    
    def is_semantics_applied(self) -> bool:
        """检查语义规则是否已应用"""
        return self._semantics_applied
    
    # === 污点分析操作 ===
    
    def run_taint_analysis(self, source: Source, sink: Sink) -> Optional[DataFlowResult]:

        self.logger.info(f"运行污点分析: 源 {source.full_name} 到汇聚点 {sink.full_name}")
        source_query = source.getQuery()
        sink_query = sink.getQuery()
        """运行污点分析"""
        cmd = f"{sink_query}.reachableByDetailed({source_query}).toJsonPretty"
        result = self._execute_command(cmd)
        if result != None:
            jsonData = result
            dataflowResult = DataFlowResult.from_joern_result(jsonData,source=source, sink=sink)
            for flow in dataflowResult.flows:
                self.logger.debug(f"数据流路径: {flow}")
                for node in flow.nodes:
                    self.fill_FlowNode(node)
            return dataflowResult
        return None

    def fill_FlowNode(self,node:FlowNode):
        self.logger.debug(f"填充FlowNode: {node}")
        function = self._get_function_by_id(node.node_id)
        if function is None:
            return
        function_code = function.code
        if function_code is None:
            self.logger.warning(f"未找到node的函数: {node.node_id}")
            return
        node.set_method_code(function_code)
        self.logger.debug(f"FlowNode {node.node_id} 的函数代码已设置: {function_code}")
    


    def execute_custom_query(self, query: str, timeout: Optional[int] = None) -> JoernQueryResult:
        """执行自定义查询"""
        return self._execute_command(query, timeout)





