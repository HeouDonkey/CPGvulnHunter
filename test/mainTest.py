import logging
from py2joern.cpgs.cpg import CPG
from py2joern.cpgs.models.function import Function
from py2joern.cpgs.models.semantics import *
from py2joern.cpgs.models.sink import Sink
from py2joern.cpgs.models.source import Source
# 在模块顶部配置日志（只需配置一次即可）
logging.basicConfig(
    level=logging.DEBUG,  # 可选: DEBUG/INFO/WARNING/ERROR/CRITICAL
    format='[%(asctime)s] %(levelname)s %(message)s'
)

class LLMBridge:
    def send(function:Function):
        print(f"Sending function to LLM: {function.full_name}")

def addSenmanticsViaLLM(cpg:CPG) ->Semantics:
    """
    通过LLM添加语义规则
    :param cpg:
    :param semantics:
    :return:
    """
    semantics = Semantics()
    for func in cpg.external_functions:
        logging.info(f"External Function: {func.full_name}")
        # 这里可以调用LLM来生成语义规则
        # 假设我们生成了一个规则，示例代码如下
        if func.full_name == "strncpy":
            logging.info(f"Adding semantics for {func.full_name}")
            semantics.add_rule(
            "strncpy",  
            [(2, 1)],      # src参数的内容传播到dest参数
            is_regex=False
            )
    logging.info(f"All semantics rules: {semantics.rules}")
    cpg.apply_semantics(semantics)
    return semantics
    

def analysis_Function(cpg:CPG):
    """
    分析函数，查找源和汇聚点
    :param cpg:
    :return:
    """    
    # 查找函数
    function_namelist = cpg._get_full_functionName_list()

    






semantics = Semantics()
semantics.add_rule(
    "strncpy",  
    [(1, 0)],      # src参数的内容传播到dest参数
    is_regex=False
)

#cpg.run_OssDataFlow(semantics)

query = """cpg.method("dangerous_sink").parameter.reachableByFlows(cpg.method.parameter.l).toJsonPretty"""

query = """cpg.method("dangerous_sink").parameter.reachableByFlows(cpg.call.argument.l).toJsonPretty"""



def find_flow(cpg:CPG):
    source:Function = cpg.find_function_by_full_name("input")
    sink:Function = cpg.find_function_by_full_name("dangerous_sink")

    source  = Source.create_from_function(source,-1)
    sink = Sink.create_from_function(sink,1)


    logging.info(f"Source: {source.getQuery()}, Sink: {sink.getQuery()}")

    cmd = sink.getQuery() + ".reachableByFlows(" + source.getQuery() + ").toJsonPretty"
    logging.info(f"Executing command: {cmd}")

    resultJson = cpg.taint_analysis(source,sink)
    print(resultJson)

"""
通过id找方法
cpg.all.filter(_.id == 115964116992L).collect {
  case cfgNode: io.shiftleft.codepropertygraph.generated.nodes.CfgNode => cfgNode
}.method.name.l

cpg.id(115964116992L).l(0).asInstanceOf[io.shiftleft.codepropertygraph.generated.nodes.CfgNode].method.name
"""

# 模拟整体流程
"""
1. 创建CPG对象
2. 传递给大模型外部方法的列表,并添加senmantics规则
3. 传递给大模型方法名，让它初步挑选其中可能的sink，source和santizer


"""
if __name__ == "__main__":
    test_src ="/home/nstl/data/vuln_hunter/py2joern/test/test_case/test1"
    # 新建cpg
    cpg = CPG(test_src)
    for func in cpg.external_functions:
        print(f"External Function: {func.full_name}")

    addSenmanticsViaLLM(cpg)
    find_flow(cpg)