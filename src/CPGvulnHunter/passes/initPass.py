from abc import ABC, abstractmethod
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from CPGvulnHunter.core.cpg import CPG
from CPGvulnHunter.models.cpg.function import Function
from CPGvulnHunter.passes.basePass import BasePass


class InitPass(BasePass):
    """
    pass base class
    onePath should init with a cpg,and then modify it.
    """

    def __init__(self,cpg: CPG) -> None:
        """
        :param src_path: the source code path
        """
        self.cpg:CPG = cpg
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")


    def _get_all_functions(self) :
        joern_wrapper = self.cpg.joern_wrapper
        if not joern_wrapper:
            self.logger.error("Joern wrapper is not initialized.")
            return
        # 获取所有函数fullName
        self.cpg.function_fullName_list = joern_wrapper.get_function_full_names(cpg_var=self.cpg.cpg_var)
        self.logger.info(f"Total function full names found: {len(self.cpg.function_fullName_list)}")
        # 获取所有函数对象
        for full_name in self.cpg.function_fullName_list:
            if not full_name:
                self.logger.warning("Function full name is empty, skipping.")
                continue
            function = self._get_single_function(full_name)
            if function and function.full_name :
                if function.is_external:
                    if function.full_name.startswith("<operator>"):
                        #operator functions add into operator_functions,and do not add into functions
                        self.cpg.operator_functions.append(function)
                    else:
                        self.cpg.external_functions.append(function)
                        self.cpg.functions.append(function)

                else:
                    self.cpg.internal_functions.append(function)
                    self.cpg.functions.append(function)
        self.logger.info(f"Total functions found: {len(self.cpg.functions)}")
        self.logger.info(f"Total external functions found: {len(self.cpg.external_functions)}")
        self.logger.info(f"Total internal functions found: {len(self.cpg.internal_functions)}")
        self.logger.info(f"Total operator functions found: {len(self.cpg.operator_functions)}")


    def _get_single_function(self,function_full_name: str) -> Optional[Function]:
        joern_wrapper = self.cpg.joern_wrapper
        if not joern_wrapper:
            self.logger.error("Joern wrapper is not initialized.")
            return None
        # 获取单个函数对象
        function = joern_wrapper.get_function_by_full_name(function_full_name, cpg_var=self.cpg.cpg_var)
        if not function:
            self.logger.error(f"Function {function_full_name} not found.")
            return None
        
        if function.full_name:
            if function.is_external:
                # fill parameter and useage for external functions,for joern cant generate signature for external functions
                if not function.full_name.startswith("<operator>"):
                    parameters = joern_wrapper.get_parameter(function, cpg_var=self.cpg.cpg_var)
                    function.set_parameters(parameters)
                    useage = joern_wrapper.find_useage(function)
                    function.set_useage(useage)                
            return function
        else:
            self.logger.warning(f"Function {function_full_name} not found.")
            return None

    def apply_external_semantics(self):
        """
        Apply semantics to external functions
        """
        if not self.cpg.llm_wrapper:
            self.logger.error("LLM wrapper is not initialized.")
            return
        
        if not self.cpg.external_functions:
            self.logger.warning("No external functions to analyze.")
            return
        # analyze external functions nad generate semantics via llm
        self.cpg.external_semantics = self.cpg.llm_wrapper.analyze_external_functions(self.cpg.external_functions)
        if not self.cpg.external_semantics:
            self.logger.error("Failed to generate semantics for external functions.")
            return
        # apply semantics to joern cpg
        if not self.cpg.joern_wrapper:
            self.logger.error("Joern wrapper is not initialized.")
            return
        self.cpg.joern_wrapper.apply_semantics(self.cpg.external_semantics)
        self.logger.info(f"Generated {len(self.cpg.external_semantics.semantic_list)} semantic rules for external functions.")




    def run(self):
        #fisrt get all functions from joern cpg,and then analyze external functions and apply semantics
        self._get_all_functions()
        self.apply_external_semantics()



