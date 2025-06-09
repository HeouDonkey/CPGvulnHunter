from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from CPGvulnHunter.core.cpg import CPG



class BasePass(ABC):
    """
    pass base class
    onePath should init with a cpg,and then modify it.
    """
    
    def __init__(self,cpg:CPG):
        self.cpg =cpg


    

    @abstractmethod
    def run(self):
        pass


