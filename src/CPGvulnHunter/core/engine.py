from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Type, Callable
import logging
from pathlib import Path
import json
import time
from datetime import datetime
import importlib

from CPGvulnHunter.core.cpg import CPG
from CPGvulnHunter.core.config import UnifiedConfig
from CPGvulnHunter.models.AnalysisResult import AnalysisResult
from CPGvulnHunter.passes.basePass import BasePass
from CPGvulnHunter.passes.initPass import InitPass
from CPGvulnHunter.passes.cwe78 import CWE78
from CPGvulnHunter.models.llm.llmConfig import LLMConfig
from CPGvulnHunter.bridges.llmWrapper import LLMWrapper




class VulnerabilityEngine:
    """
    CPG漏洞分析引擎
    
    核心职责：
    1. 管理CPG生命周期
    2. 协调分析passes执行
    3. 收集和处理分析结果
    4. 生成漏洞报告
    """
    
    def __init__(self, 
                 src_path: str,
                 config_file: Optional[str] = None,
                 config: Optional[UnifiedConfig] = None):
        """
        初始化漏洞分析引擎
        
        Args:
            src_path: 源代码路径
            config_file: 配置文件路径
            config: 统一配置对象（与config_file二选一）
        """
        self.src_path = src_path
        
        # 加载配置
        if config is not None:
            self.config = config
        elif config_file is not None:
            self.config = UnifiedConfig.from_file(config_file)
        else:
            # 尝试使用默认配置文件
            default_config_file = "config.yml"
            if Path(default_config_file).exists():
                self.config = UnifiedConfig.from_file(default_config_file)
            else:
                self.config = UnifiedConfig()
        
        # 设置日志
        self.config.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info(f"初始化漏洞分析引擎 - 源路径: {src_path}")
        self.logger.debug(f"配置文件: {config_file}")
        self.logger.debug(f"启用的分析passes: {self.config.engine.enabled_passes}")
        self.logger.debug(f"最大调用深度: {self.config.engine.max_call_depth}")
        self.logger.debug(f"并行执行: {self.config.engine.parallel_execution}")
        
        # 验证配置
        config_errors = self.config.validate()
        if config_errors:
            self.logger.warning(f"发现 {len(config_errors)} 个配置问题:")
            for error in config_errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info("配置验证通过")
        
        # 初始化CPG
        self.logger.info("开始初始化CPG...")
        cpg_start_time = time.time()
        self.cpg = CPG.from_config(src_path, self.config)
        cpg_init_time = time.time() - cpg_start_time
        self.logger.info(f"CPG初始化完成，耗时: {cpg_init_time:.2f}秒")
        
        # 记录CPG统计信息
        self.logger.info(f"CPG统计信息:")
        self.logger.info(f"  - 总函数数: {len(self.cpg.functions)}")
        self.logger.info(f"  - 内部函数数: {len(self.cpg.internal_functions)}")
        self.logger.info(f"  - 外部函数数: {len(self.cpg.external_functions)}")
        if hasattr(self.cpg, 'operator_functions'):
            self.logger.info(f"  - 操作符函数数: {len(self.cpg.operator_functions)}")
        
        # 记录主要的外部函数
        if self.cpg.external_functions:
            ext_func_names = [func.name for func in self.cpg.external_functions[:10]]  # 只显示前10个
            self.logger.debug(f"主要外部函数: {ext_func_names}")
            if len(self.cpg.external_functions) > 10:
                self.logger.debug(f"  ... 还有 {len(self.cpg.external_functions) - 10} 个外部函数")
        
        # 分析结果
        self.results: List[AnalysisResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # 从配置文件中加载Pass注册表
        self.pass_registry: Dict[str, str] = self.config.engine.pass_registry

        # 创建输出目录
        self.output_dir = Path(self.config.engine.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"输出目录: {self.output_dir.absolute()}")
        
        self.logger.info("引擎初始化完成")
    
    def run_analysis(self) -> List[AnalysisResult]:
        """
        执行完整的漏洞分析流程
        
        Returns:
            List[AnalysisResult]: 分析结果列表
        """
        self.logger.info("=" * 60)
        self.logger.info("开始执行漏洞分析")
        self.logger.info("=" * 60)
        self.start_time = time.time()
        
        try:
            # 获取启用的passes
            enabled_passes = self.config.engine.enabled_passes
            self.logger.info(f"分析配置:")
            self.logger.info(f"  - 启用的passes: {enabled_passes} (共 {len(enabled_passes)} 个)")
            self.logger.info(f"  - 并行执行: {self.config.engine.parallel_execution}")
            self.logger.info(f"  - 每个pass超时: {self.config.engine.timeout_per_pass}秒")
            self.logger.info(f"  - 最大函数数: {self.config.engine.max_functions}")
            
            # 初始化执行统计
            successful_passes = 0
            failed_passes = 0
            total_findings = 0
            
            # 按顺序执行各个pass
            for i, pass_name in enumerate(enabled_passes, 1):
                self.logger.info(f"\n--- 执行Pass {i}/{len(enabled_passes)}: {pass_name} ---")
                result = self._execute_pass(pass_name)
                self.results.append(result)
                
                # 更新统计
                if result.success:
                    successful_passes += 1
                    total_findings += len(result.findings)
                    self.logger.info(f"✓ Pass {pass_name} 执行成功")
                    if result.findings:
                        self.logger.info(f"  发现 {len(result.findings)} 个漏洞")
                    else:
                        self.logger.info("  未发现漏洞")
                else:
                    failed_passes += 1
                    self.logger.error(f"✗ Pass {pass_name} 执行失败: {result.errors}")
                    if not self.config.engine.parallel_execution:
                        self.logger.warning("非并行模式下遇到错误，停止后续pass执行")
                        break
            
            self.end_time = time.time()
            total_time = self.end_time - self.start_time
            
            # 输出详细的分析摘要
            self.logger.info("\n" + "=" * 60)
            self.logger.info("分析完成 - 执行摘要")
            self.logger.info("=" * 60)
            self.logger.info(f"总耗时: {total_time:.2f}秒")
            self.logger.info(f"执行的passes: {len(self.results)}/{len(enabled_passes)}")
            self.logger.info(f"成功的passes: {successful_passes}")
            self.logger.info(f"失败的passes: {failed_passes}")
            self.logger.info(f"总计发现漏洞: {total_findings}")
            
            # 按pass显示详细结果
            for result in self.results:
                status = "成功" if result.success else "失败"
                self.logger.info(f"  - {result.pass_name}: {status} ({result.execution_time:.2f}s, {len(result.findings)}个发现)")
            
            # 保存结果
            if self.config.engine.save_intermediate_results:
                self.logger.info("\n保存分析结果...")
                self._save_results()
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"分析过程中发生严重错误: {e}")
            self.logger.exception("详细错误信息:")
            raise
    
    def _get_pass_class(self, pass_name: str):
        """
        根据pass名称动态加载类
        """
        if pass_name not in self.pass_registry:
            raise ValueError(f"未知的Pass: {pass_name}")

        module_path, class_name = self.pass_registry[pass_name].rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def _execute_pass(self, pass_name: str) -> AnalysisResult:
        """
        执行单个分析pass
        
        Args:
            pass_name: Pass名称
            
        Returns:
            AnalysisResult: 该pass的执行结果
        """
        self.logger.info(f"执行Pass: {pass_name}")
        start_time = time.time()
        
        try:
            # 动态加载Pass类
            pass_class = self._get_pass_class(pass_name)
            pass_instance = pass_class(self.cpg)

            # 执行pass
            if hasattr(pass_instance, 'run'):
                pass_instance.run()
                result_info = pass_instance.get_analysis_results() if hasattr(pass_instance, 'get_analysis_results') else {}
            else:
                result_info = []
                self.logger.warning(f"Pass {pass_name} 没有run方法")
            
            execution_time = time.time() - start_time
            
            result = AnalysisResult(
                pass_name=pass_name,
                success=True,
                execution_time=execution_time,
                metadata={"cpg_functions": len(self.cpg.functions)},
                result_info=result_info if isinstance(result_info, dict) else {}
            )
            
            self.logger.info(f"Pass {pass_name} 执行成功，耗时: {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Pass {pass_name} 执行失败: {str(e)}"
            self.logger.error(error_msg)
            
            return AnalysisResult(
                pass_name=pass_name,
                success=False,
                execution_time=execution_time,
                errors=[error_msg]
            )
    
    def _save_results(self):
        """保存分析结果"""
        try:
            # 创建结果摘要
            summary = {
                "analysis_summary": {
                    "src_path": self.src_path,
                    "total_execution_time": self.end_time - self.start_time if self.end_time and self.start_time else 0,
                    "total_passes": len(self.results),
                    "successful_passes": sum(1 for r in self.results if r.success),
                    "failed_passes": sum(1 for r in self.results if not r.success),
                    "timestamp": datetime.now().isoformat()
                },
                "cpg_info": {
                    "total_functions": len(self.cpg.functions),
                    "external_functions": len(self.cpg.external_functions),
                    "internal_functions": len(self.cpg.internal_functions)
                },
                "config": self.config.to_dict(),
                "pass_results": [
                    {
                        "pass_name": result.pass_name,
                        "success": result.success,
                        "execution_time": result.execution_time,
                        "findings_count": len(result.findings),
                        "errors_count": len(result.errors),
                        "findings": result.findings,
                        "errors": result.errors,
                        "metadata": result.metadata
                    }
                    for result in self.results
                ]
            }
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_results_{timestamp}.json"
            output_file = self.output_dir / filename
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"分析结果已保存到: {output_file}")
            
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取分析结果摘要
        
        Returns:
            Dict[str, Any]: 摘要信息
        """
        if not self.results:
            return {"status": "no_analysis_run"}
        
        total_findings = sum(len(result.findings) for result in self.results)
        total_errors = sum(len(result.errors) for result in self.results)
        total_time = sum(result.execution_time for result in self.results)
        
        return {
            "total_passes": len(self.results),
            "successful_passes": sum(1 for r in self.results if r.success),
            "failed_passes": sum(1 for r in self.results if not r.success),
            "total_findings": total_findings,
            "total_errors": total_errors,
            "total_execution_time": total_time,
            "src_path": self.src_path,
            "cpg_functions": len(self.cpg.functions)
        }


def quick_analysis(src_path: str, 
                  config_file: Optional[str] = None,
                  passes: Optional[List[str]] = None) -> List[AnalysisResult]:
    """
    便利函数：一键执行漏洞分析
    
    Args:
        src_path: 源代码路径
        config_file: 配置文件路径
        passes: 要执行的passes列表
        
    Returns:
        List[AnalysisResult]: 分析结果
    """
    # 创建配置
    if config_file:
        config = UnifiedConfig.from_file(config_file)
    else:
        config = UnifiedConfig()
    
    # 覆盖passes配置
    if passes:
        config.engine.enabled_passes = passes
    
    # 创建引擎并执行分析
    engine = VulnerabilityEngine(src_path, config=config)
    return engine.run_analysis()



if __name__ == "__main__":
    # 示例：快速分析
    src_path = "/home/nstl/data/CPGvulnHunter/test/test_case/test2"
    config_file = "/home/nstl/data/CPGvulnHunter/config.yml"
    engine = VulnerabilityEngine(src_path=src_path,config_file=config_file)
    engine.run_analysis()
