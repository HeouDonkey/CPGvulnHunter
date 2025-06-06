from abc import ABC, abstractmethod
from py2joern.cpgs.models.flowPath import DataFlowResult, FlowPath
from py2joern.joernBridge.joernBridge import JoernBridge
import os
from py2joern.cpgs.models.function import Function, Parameter
from py2joern.cpgs.models.semantics import Semantics
import logging
import re
import json

from py2joern.cpgs.models.sink import Sink
from py2joern.cpgs.models.source import Source

class CPG:
    """
    用来表征一个cpg，抽象类可以继承，针对不同的语言做。
    """

    def __init__(self, src_path: str,cpg :str ='cpg' ):
        self.joern:JoernBridge  = JoernBridge('/home/nstl/data/vuln_hunter/heouJoern/joern/joern-cli/target/universal/stage/joern')
        self.src_path = src_path
        self.cpg_var = cpg
        self.functions:list[Function] = []
        self.external_functions:list[Function] = []
        self.internal_functions:list[Function] = []
        self.operator_functions:list[Function] = []
        self.sinks = []
        self.sources = []
        self.function_fullName_list = []
        self._import_code(self.src_path)
        self._get_full_functionName_list()
        self._get_all_functions()
        self.external_semantics: Semantics = Semantics()
        self.dataflowResults: list[DataFlowResult] = []

    def _import_code(self, src_path: str) -> bool:
        """
        导入源代码到CPG中。
        :param src_path: 源代码路径
        :return: 是否成功导入
        """
        cmd  = f"""importCode("{src_path}")"""
        logging.info(f"Importing code from {src_path} with command: {cmd}")
        result = self.joern.send_command(cmd)
        logging.info(f"Import result: {result}")
        return result
    
    def _get_full_functionName_list(self) -> list:
        """
        获取CPG中所有函数的全名列表。
        :return: 函数全名列表
        """
        cmd = "cpg.method.fullName.toJsonPretty"
        result = self.joern.send_command(cmd)
        match = re.search(r'"""(.*?)"""', result, re.DOTALL)
        if match:
            json_str = match.group(1)
            result_list = json.loads(json_str)
            self.function_fullName_list = result_list
            print(result_list)
        else:
            print("未找到内容")
        return result_list


    def _get_all_functions(self) -> list:
        for function_name in self.function_fullName_list:
            function = self._get_function_by_name(function_name)
            if function:
                if function.is_external:
                    if function.full_name.startswith("<operator>"):
                        self.operator_functions.append(function)
                    else:
                        self.external_functions.append(function)
                        self.functions.append(function)

                else:
                    self.internal_functions.append(function)
                    self.functions.append(function)

        logging.debug(f"获取到 {len(self.functions)} 个函数")
        logging.debug(f"函数列表: {[func.to_dict for func in self.functions]}")
        return self.functions

    def _get_function_by_name(self, name: str) -> Function:
        """
        根据函数名获取CPG中的函数对象。
        :param name: 函数名
        :return: 函数对象
        """
        cmd = f'cpg.method.fullName("{name}").toJsonPretty'
        result = self.joern.send_command(cmd)
        match = re.search(r'"""(.*?)"""', result, re.DOTALL)
        if match:
            json_str = match.group(1)
            function_data = json.loads(json_str)
            logging.debug(f"获取函数 {name} 的数据: {function_data}")
            function = Function.from_json(function_data)
            parameters:list[Parameter] = self._load_parameters(function)
            function.set_parameters(parameters)
            usage = self._load_useage(function)
            function.set_useage(usage)
            logging.debug(f"函数 {name} 的参数列表: {[param.to_dict for param in function.parameters]}")
            return function

        else:
            logging.error(f"未找到函数 {name}")
            return None

    def _load_parameters(self, function: Function) -> list[Parameter]:
        """
        加载并填充函数的参数列表。
        :param function: 函数对象
        :return: 参数列表
        """
        cmd = function.generateParameterQuery()
        result = self.joern.send_command(cmd)
        match = re.search(r'"""(.*?)"""', result, re.DOTALL)
        if match:
            json_str = match.group(1)
            parameter_list_json = json.loads(json_str)
            
            # 创建 Parameter 对象列表
            parameter_list = []
            for param_json in parameter_list_json:
                p = Parameter.from_json(param_json)
                parameter_list.append(p)
            
            return parameter_list
        else:
            logging.error(f"未找到参数")
            return []

    def _load_useage(self, function: Function) -> str:
        cmd = function.generateUseageQuery()
        result = self.joern.send_command(cmd)
        match = re.search(r'"""(.*?)"""', result, re.DOTALL)
        if match:
            json_str = match.group(1)
            useage_data = json.loads(json_str)
            logging.debug(f"函数 {function.full_name} 的使用情况: {useage_data}")
            return useage_data
        else:
            logging.error(f"未找到函数 {function.full_name} 的使用情况")
            return None


    def apply_semantics(self):
        """
        执行数据流分析。
        :param semantics: 语义规则
        :return: 数据流分析结果
        """
        try:
            # 1. 测试连接
            test_result = self.joern.send_command("1 + 1")
            logging.debug(f"连接测试结果: {test_result}")
            
            # 2. 逐步导入必要的类
            imports = [
                "import io.joern.dataflowengineoss.*",
                "import io.joern.dataflowengineoss.semanticsloader.*",
                "import io.joern.dataflowengineoss.queryengine.*",
            ]
            
            for import_cmd in imports:
                result = self.joern.send_command(import_cmd)
                logging.debug(f"执行导入: {import_cmd} -> {result}")
                if "error" in result.lower() or "exception" in result.lower():
                    logging.error(f"导入失败: {import_cmd} -> {result}")
            
            # 3. 定义语义规则
            extraFlows = self.external_semantics.get_extraFlows()
            if extraFlows.strip():
                logging.info("定义语义规则...")
                result2 = self.joern.send_command(extraFlows)
                logging.debug(f"语义规则定义结果: {result2}")
            
            # 4. 创建上下文
            context_cmd = f"implicit val semantics: Semantics = DefaultSemantics().plus(extraFlows)"
            logging.info("创建上下文...")
            result3 = self.joern.send_command(context_cmd) 
            logging.debug(f"上下文创建结果: {result3}")
            

            options_cmd = "implicit val context: EngineContext = EngineContext(maxCallDepth = 40,semantics = semantics)"

            
            logging.info("创建数据流选项...")
            result4 = self.joern.send_command(options_cmd)
            logging.debug(f"选项创建结果: {result4}")
        except Exception as e:
            logging.error(f"数据流分析执行失败: {e}")
            import traceback
            logging.error(f"错误堆栈: {traceback.format_exc()}")
            return ""

    def taint_analysis(self,source:Source,sink:Sink,) -> list[DataFlowResult]:
        cmd = sink.getQuery() + ".reachableByDetailed(" + source.getQuery() + ").toJsonPretty"
        output = self.joern.send_command(cmd)
        logging.debug(f"Taint analysis output: {output}")
        result = self.joern.send_command(cmd)
        match = re.search(r'"""(.*?)"""', result, re.DOTALL)
        if match:
            json_str = match.group(1)
            dataflowResult = DataFlowResult.from_joern_result(json_str)
            if dataflowResult:
                self.dataflowResults.append(dataflowResult)
                logging.info(f"数据流分析结果: {dataflowResult}")
            return dataflowResult
            
        else:
            logging.error(f"未找到流路径数据")  
            return None
    

  

    def find_function_by_full_name(self,target_full_name: str) -> Function:
        """根据完整名称查找单个函数"""
        for func in self.functions:
            if func.full_name == target_full_name:
                return func
        return None
            
    """
    val extraFlows = List(
        FlowSemantic.from(
            "^path.*<module>\\.sanitizer$", // Method full name
            List((1, 1)), // Flow mappings
            regex = true  // Interpret the method full name as a regex string
        )
    )
    val context = new LayerCreatorContext(cpg)
    val options = new OssDataFlowOptions(semantics = DefaultSemantics().plus(extraFlows))
    new OssDataFlow(options).run(context)
    """
   
