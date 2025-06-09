import logging


# 在模块顶部配置日志（只需配置一次即可）
logging.basicConfig(
    level=logging.DEBUG,  # 可选: DEBUG/INFO/WARNING/ERROR/CRITICAL
    format='[%(asctime)s] %(levelname)s %(message)s'
)



    

def analysis_Function(cpg:CPG):
    """
    分析函数，查找源和汇聚点
    :param cpg:
    :return:
    """    
    # 查找函数
    externalFunctions = cpg.external_functions
    client = LlamaClient(api_key=key)
    LLMBridge = VulnerabilityLLMBridge(client)
    for func in externalFunctions:
        request = FunctionPrompt.build_semantic_analysis_request(func)
        result = client.send(request)
        print(result)




if __name__ == "__main__":
    test_src ="/home/nstl/data/vuln_hunter/py2joern/test/test_case/test1"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjBjN2ZjYWI0LWNkYTctNDQ5MC04Y2VkLThmZDNjNDQ0ODM4MyJ9.EF4VyeqVO0rfgN5mpFWYYZEaarcOXSQ1vjw-UYVCfkI"

    # 新建cpg
    cpg = CPG(test_src)
    for func in cpg.functions:
        print(func.toJson())
    analysis_Function(cpg)