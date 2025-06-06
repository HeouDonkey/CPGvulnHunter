import logging
import os
import yaml
from pathlib import Path
from py2joern.cpgs.cpg import CPG
from py2joern.cpgs.models.sink import Sink
from py2joern.cpgs.models.source import Source
from py2joern.llmBridge.clients.lamaClient import LamaClient
from py2joern.llmBridge.core.llmBridge import VulnerabilityLLMBridge
from py2joern.vulnPasses.cwe78 import CWE78


class Hunt():
    def __init__(self, src_path: str):
        self.config = self.load_config()
        self.src_path = src_path
        self.client = LamaClient(**self.config.get('llm_client', {}))
        self.llmBridge = VulnerabilityLLMBridge(self.client)
        self.cpg = CPG(self.src_path)
        self.external_semantics = None


    def run(self):
        """
        1.分析外部方法的数据流
        """
        external_functions = self.cpg.external_functions
        if not external_functions:
            print("没有外部函数可供分析")
            return
        
        # 分析外部函数并生成语义规则
        semantics = self.llmBridge.analyze_external_functions(external_functions)
        self.external_semantics = semantics
        self.cpg.external_semantics = semantics
        logging.info(f"生成的语义规则数量: {len(semantics.semantic_list)}")
        logging.debug(f"生成的语义规则: {semantics}")
        # 将语义规则应用到数据流分析中
        self.cpg.apply_semantics()
        CWE78(cpg=self.cpg, llmBridge=self.llmBridge).run()
        print("数据流分析完成，语义规则已应用。")

        logging.debug(self.cpg.dataflowResults[0])
    
  

    def load_config(self):
        """加载配置文件"""
        # 获取项目根目录（从当前文件向上4级目录）
        project_root = Path(__file__).parent.parent.parent
        
        # 从环境变量获取配置路径，或使用默认的 config.yml
        config_path = os.path.join(project_root, 'config.yml')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)




if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,  # 可选: DEBUG/INFO/WARNING/ERROR/CRITICAL
        format='[%(asctime)s] %(levelname)s %(message)s'
    )
    test_src = "/home/nstl/data/vuln_hunter/py2joern/test/test_case/test2"
    hunt = Hunt(test_src)
    hunt.run()