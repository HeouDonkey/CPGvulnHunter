from py2joern.llmBridge.clients.lamaClient import LlamaClient
from py2joern.llmBridge.models.dataclass import LLMRequest, AnalysisType
from py2joern.cpgs.models.function import Function
from py2joern.llmBridge.models.prompt import FunctionPrompt

if __name__ == "__main__":
    functionJson = """[
  {
    "name":"fgets",
    "astParentFullName":"<global>",
    "_id":111669149705,
    "signature":"",
    "astParentType":"NAMESPACE_BLOCK",
    "_label":"METHOD",
    "fullName":"fgets",
    "genericSignature":"<empty>",
    "code":"<empty>",
    "isExternal":true,
    "order":0,
    "filename":"<empty>"
  }
]"""
    func = Function.from_json(functionJson)

    # 构建语义分析请求
    request = FunctionPrompt.build_semantic_analysis_request(func)
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjBjN2ZjYWI0LWNkYTctNDQ5MC04Y2VkLThmZDNjNDQ0ODM4MyJ9.EF4VyeqVO0rfgN5mpFWYYZEaarcOXSQ1vjw-UYVCfkI"
    # 测试LlamaClient
    client = LlamaClient("http://192.168.5.253:3000/api/",api_key=key)
    
    models = client.get_available_models()
    print("可用模型:", models)
    response = client.send(request)

    # 打印请求内容
    print(request)