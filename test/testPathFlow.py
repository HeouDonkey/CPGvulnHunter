import sys
sys.path.insert(0, 'src')

from py2joern.models.flowPath import FlowNode, FlowPath, DataFlowResult,NodeType

def test_new_flow_models():
    print("=" * 60)
    print("测试新的 FlowPath 模型")
    print("=" * 60)
    
    # 使用您提供的JSON数据进行测试
    test_json = '''[
  {
    "path":[
      {
        "node":{
          "dynamicTypeHintFullName":[],
          "_id":128849018882,
          "evaluationStrategy":"BY_VALUE",
          "code":"RET",
          "typeFullName":"char*",
          "lineNumber":18,
          "order":2,
          "_label":"METHOD_RETURN",
          "possibleTypes":[],
          "columnNumber":1
        },
        "callSiteStack":[],
        "visible":true,
        "isOutputArg":false,
        "outEdgeLabel":""
      },
      {
        "node":{
          "name":"input",
          "_id":30064771081,
          "signature":"",
          "code":"input()",
          "typeFullName":"char*",
          "lineNumber":28,
          "order":2,
          "methodFullName":"input",
          "_label":"CALL",
          "dynamicTypeHintFullName":[],
          "dispatchType":"STATIC_DISPATCH",
          "columnNumber":11,
          "possibleTypes":[],
          "argumentIndex":2
        },
        "callSiteStack":[],
        "visible":true,
        "isOutputArg":false,
        "outEdgeLabel":"input()"
      },
      {
        "node":{
          "dynamicTypeHintFullName":[],
          "name":"ptr",
          "_id":68719476743,
          "code":"ptr",
          "typeFullName":"char*",
          "lineNumber":28,
          "order":1,
          "_label":"IDENTIFIER",
          "columnNumber":5,
          "possibleTypes":[],
          "argumentIndex":1
        },
        "callSiteStack":[],
        "visible":true,
        "isOutputArg":false,
        "outEdgeLabel":"ptr"
      }
    ]
  }
]'''
    
    # 解析结果
    result = DataFlowResult.from_joern_result(test_json)
    
    print(f"解析结果:")
    print(result.get_summary())
    
    if result.flows:
        flow = result.flows[0]
        print(f"\n第一个数据流:")
        print(f"  {flow.get_path_summary()}")
        print(f"  路径长度: {flow.path_length}")
        print(f"  源节点: {flow.source}")
        print(f"  汇聚节点: {flow.sink}")
        
        print(f"\n详细路径:")
        print(flow.get_detailed_path())
        
        print(f"\n经过的行号: {flow.get_line_numbers()}")
        
        # 测试节点类型查询
        call_nodes = flow.get_nodes_by_type(NodeType.CALL)
        print(f"\nCALL节点数量: {len(call_nodes)}")
        for node in call_nodes:
            print(f"  {node}")

if __name__ == '__main__':
    test_new_flow_models()